// SPDX-License-Identifier: GPL-3.0-or-later

#include "AlienCommandAudit.h"
#include "../Engine/Logger.h"
#include "../Engine/Options.h"
#include "AlienCommandModel.h"
#include "../Engine/RNG.h"
#include "../Mod/Mod.h"
#include "../Mod/RuleAlienMission.h"
#include "../Mod/RuleMissionScript.h"
#include "../Mod/RuleRegion.h"
#include "../Savegame/AlienMission.h"
#include "../Savegame/GameTime.h"
#include "../Savegame/Ufo.h"
#include <exception>
#include <set>
#include <memory>
#include <algorithm>
#include "../Engine/Game.h"
#include "../Engine/Yaml.h"
#include "../Savegame/SavedGame.h"
#include "../Mod/UfoTrajectory.h"

namespace OpenXcom
{
std::vector<AlienReconCandidate> buildAlienPortfolioMenu(const Mod &mod, const SavedGame &save)
{
 std::vector<AlienReconCandidate> result;
 std::set<std::pair<std::string,std::string>> operationalRegions;
 for (const auto &mission : {"STR_ALIEN_RESEARCH","STR_ALIEN_PROBE_MISSION","STR_ALIEN_HARVEST","STR_ALIEN_ABDUCTION","STR_ALIEN_TERROR","STR_ALIEN_SURFACE_ATTACK","STR_ALIEN_RETALIATION"})
 {
  const auto *rule=mod.getAlienMission(mission);
  if (!rule || !rule->getWaveCount() || !rule->hasRaceWeights() || rule->getOperationType()!=AMOT_SPACE || rule->skipScoutingPhase()) continue;
  for (const auto &name:mod.getRegionsList())
  {
   const auto *r=mod.getRegion(name);
   const auto *geo=r->getMissionRegion().empty()?r:mod.getRegion(r->getMissionRegion());
   if (!geo || r->getWeight()<=0) continue;
   const auto &weights=r->getAvailableMissions().getChoicesRaw();
   auto w=weights.find(mission);
   if (rule->getObjective()==OBJECTIVE_SCORE && (w==weights.end() || w->second<=0)) continue;
   bool valid=true;
   for (size_t i=0;i<rule->getWaveCount();++i)
   {
    const auto &wave=rule->getWave(i); const auto *t=mod.getUfoTrajectory(wave.trajectory);
    if (!t || !mod.getUfo(wave.ufoType)) {valid=false;break;}
    for (size_t j=0;j<t->getWaypointCount();++j)
     if (t->getZone(j)>=geo->getMissionZones().size() || geo->getMissionZones()[t->getZone(j)].areas.empty()) valid=false;
   }
   if (rule->getObjective()==OBJECTIVE_SITE && (rule->getSpawnZone()<0 || (size_t)rule->getSpawnZone()>=geo->getMissionZones().size() || geo->getMissionZones()[rule->getSpawnZone()].areas.empty())) valid=false;
   for (const auto *existing:save.getAlienMissions())
    if (existing->getRules().getType()==mission && existing->getRegion()==geo->getType()) valid=false;
   if (valid && operationalRegions.emplace(mission,geo->getType()).second) result.push_back({mission,name});
  }
 }
 return result;
}
void executeAlienPortfolio(Game &game, const Globe &globe)
{
 auto &save=*game.getSavedGame(); auto &ledger=save.getAlienCommand(); auto &mod=*game.getMod();
 ledger.beginBudgetMonth(std::max(0,save.getMonthsPassed()),(int)save.getDifficulty());
 if (!ledger.portfolioDue()) return;
 auto menu=buildAlienPortfolioMenu(mod,save);
 std::vector<AlienReconCandidate> regions;
 for (const auto &region:mod.getRegionsList()) regions.push_back({"REGION",region});
 auto input=ledger.snapshot(regions); input.candidates=menu;
 const auto body="{\"schemaVersion\":1,\"budget\":"+ledger.budgetJson()+",\"knowledge\":"+AlienCommand::inputJson(input)+"}";
 auto response=queryAlienPortfolioModel(body,Options::alienCommandModelPort);
 std::string status="MODEL_UNAVAILABLE_SAVE_RESOURCES";
 std::vector<AlienReconCandidate> selected;
 try
 {
  YAML::YamlRootNodeReader r(YAML::YamlString(response),"alien portfolio response");
  if (r["schemaVersion"].readVal<int>()!=1 || r["protocol"].readVal<std::string>()!="alien-portfolio-laya-v1"
    || r["checkpointSha256"].readVal<std::string>()!="bcbb891d21cf081a9d7a941b97f8b0f10cf3dac7473b4b9450fab0d07b885175") throw std::runtime_error("Portfolio identity mismatch");
  const auto modelStatus=r["status"].readVal<std::string>();
  if (modelStatus!="PREDICTED" && modelStatus!="SAVE_RESOURCES") throw std::runtime_error("Portfolio inference unavailable");
  auto ops=r["operations"].children(); if (ops.size()>3) throw std::runtime_error("Portfolio exceeds operation limit");
  std::set<std::pair<std::string,std::string>> seen;
  int totalCost=0;
  for (const auto &op:ops)
  {
   AlienReconCandidate c{op["mission"].readVal<std::string>(),op["region"].readVal<std::string>()};
   const auto *region=mod.getRegion(c.region);
   const auto actualRegion=region && !region->getMissionRegion().empty()?region->getMissionRegion():c.region;
   if (!seen.emplace(c.mission,actualRegion).second || !std::any_of(menu.begin(),menu.end(),[&](const auto &m){return m.mission==c.mission && m.region==c.region;})
     || !ledger.canFund(c.mission)) throw std::runtime_error("Invalid/unaffordable portfolio");
   totalCost+=AlienCommand::operationCost(c.mission);
   if (totalCost>ledger.remainingBudget()) throw std::runtime_error("Portfolio exceeds total budget");
   selected.push_back(c);
  }
  if (modelStatus=="SAVE_RESOURCES" && !selected.empty()) throw std::runtime_error("Inconsistent portfolio status");
  // Validate the entire portfolio before consuming RNG or reserving a real mission.
  std::vector<std::unique_ptr<AlienMission>> ready;
  for (const auto &c:selected)
  {
   const auto *rule=mod.getAlienMission(c.mission);
   auto mission=std::make_unique<AlienMission>(*rule);
   mission->setRegion(c.region,mod); mission->setRace(rule->generateRace(std::max(0,save.getMonthsPassed())));
   if (!mod.getAlienRace(mission->getRace())) throw std::runtime_error("Portfolio has unavailable race");
   mission->setId(save.getId("ALIEN_MISSIONS"));
   if (rule->getObjective()==OBJECTIVE_SITE)
   {
    const auto &areas=mod.getRegion(mission->getRegion())->getMissionZones()[rule->getSpawnZone()].areas;
    mission->setMissionSiteZoneArea(RNG::generate(0,areas.size()-1));
   }
   ready.push_back(std::move(mission));
  }
  auto reserved=ledger;
  for (const auto &mission:ready)
   if (!reserved.fundMission(mission->getId(),mission->getRules().getType())) throw std::runtime_error("Portfolio reservation failed");
  ledger=std::move(reserved);
  for (auto &mission:ready) { mission->start(game,globe); save.getAlienMissions().push_back(mission.release()); }
  status=selected.empty()?"SAVED_RESOURCES":"PORTFOLIO_EXECUTED";
 }
 catch (const std::exception &) { if (!response.empty()) status="REJECTED_PORTFOLIO_SAVE_RESOURCES"; }
 ledger.recordPortfolio(save.getTime()->getFullString(),body,response,status);
 Log(LOG_INFO)<<"AlienCommandAudit "<<ledger.getAudit().back();
}
std::vector<AlienReconCandidate> buildAlienReconMenu(const Mod &mod)
{
	std::vector<AlienReconCandidate> result;
	// Distinct information-gathering operations: contact gathering and engine base search.
	for (const auto &mission : { "STR_ALIEN_RESEARCH", "STR_ALIEN_PROBE_MISSION", "STR_ALIEN_RETALIATION" })
	{
		const auto *rules = mod.getAlienMission(mission);
		if (!rules || (rules->getObjective() != OBJECTIVE_SCORE && rules->getObjective() != OBJECTIVE_RETALIATION)) continue;
		if (rules->getObjective() == OBJECTIVE_RETALIATION && rules->skipScoutingPhase()) continue;
		for (const auto &region : mod.getRegionsList())
		{
			const auto *r = mod.getRegion(region);
			const auto &weights = r->getAvailableMissions().getChoicesRaw();
			const auto found = weights.find(mission);
			const auto *geography = r->getMissionRegion().empty() ? r : mod.getRegion(r->getMissionRegion());
			if (r->getWeight() > 0 && (rules->getObjective() == OBJECTIVE_RETALIATION || (found != weights.end() && found->second > 0))
				&& geography && !geography->getMissionZones().empty())
				result.push_back({mission, region});
		}
	}
	return result;
}

AlienInterceptionContact captureAlienInterceptionContact(const Mod &mod, const Ufo &ufo, const GameTime &time)
{
	AlienInterceptionContact contact;
	contact.observed = true;
	contact.ufoId = ufo.getUniqueId();
	contact.missionId = ufo.getMission() ? ufo.getMission()->getId() : 0;
	contact.observedAt = time.getFullString();
	contact.longitude = ufo.getLongitude();
	contact.latitude = ufo.getLatitude();
	for (const auto &region : mod.getRegionsList())
	{
		if (mod.getRegion(region)->insideRegion(contact.longitude, contact.latitude))
		{
			contact.region = region;
			break;
		}
	}
	return contact;
}

AlienCommandMissionAudit::AlienCommandMissionAudit(AlienCommand *command, const Mod &mod,
	const RuleMissionScript &script, const std::string &time, int difficulty) :
	_command(command), _time(time), _script(script.getType()), _scope("BASELINE_ONLY"),
	_difficulty(difficulty), _exceptions(std::uncaught_exceptions())
{
	if (!_command) return;
	_execution.rngBefore = RNG::getSeed();
	// Modified scripts with target-base or region/mission overrides stay baseline-only.
	if (script.getType() == "recon" && !script.getSiteType() && script.getTargetBaseOdds() == 0
		&& !script.hasRegionWeights() && !script.hasMissionWeights())
	{
		_scope = "RECON";
		_input = _command->snapshot(buildAlienReconMenu(mod));
		_proposal = AlienCommand::chooseRecon(_input);
		if (Options::alienCommandModelPort != 0) _model = queryAlienReconModel(_input, Options::alienCommandModelPort);
	}
	else
		_proposal.reason = "SCRIPT_OUT_OF_SCOPE";
}

AlienCommandMissionAudit::~AlienCommandMissionAudit() noexcept
{
	if (!_command) return;
	try
	{
		if (std::uncaught_exceptions() > _exceptions) _execution.status = "ENGINE_EXCEPTION";
		_execution.rngAfter = RNG::getSeed();
		_command->recordDecision(_time, _difficulty, _script, _scope, _input, _proposal, _execution, _model);
		Log(LOG_INFO) << "AlienCommandAudit " << _command->getAudit().back();
	}
	catch (...)
	{
		// An audit failure cannot replace a completed legacy mission or mask its exception.
	}
}

bool AlienCommandMissionAudit::executableProposal(AlienReconProposal &proposal) const
{
	if (!Options::alienCommandModelExecute || !_command || _scope != "RECON"
		|| _model.status != "MODEL_PROPOSAL_VALID_SHADOW_ONLY"
		|| !AlienCommand::validateProposal(_input, _model.proposal)) return false;
	proposal = _model.proposal;
	return true;
}

void AlienCommandMissionAudit::operationalStatus(const std::string &status)
{
	_execution.operationalStatus = status;
}

void AlienCommandMissionAudit::executed(int id, const std::string &mission,
	const std::string &region, const std::string &race)
{
	_execution.status = "MISSION_CREATED";
	if (_execution.operationalStatus == "MODEL_OPERATION_SELECTED")
	{
		_execution.source = "MODEL_COMMANDER";
		_model.status = "MODEL_PROPOSAL_EXECUTED";
	}
	_execution.missionId = id;
	_execution.mission = mission;
	_execution.region = region;
	_execution.race = race;
}
}
