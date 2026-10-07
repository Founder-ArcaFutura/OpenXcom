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
namespace
{
std::vector<int> portfolioSiteAreas(const RuleAlienMission &rule,const RuleRegion &region)
{
 std::vector<int> result;
 const int zone=rule.getSpawnZone();
 if(zone<0 || (size_t)zone>=region.getMissionZones().size())return result;
 const auto &areas=region.getMissionZones()[zone].areas;
 for(size_t i=0;i<areas.size();++i)
  if(areas[i].isPoint() || areas[i].texture<0 || !rule.getSiteType().empty())result.push_back((int)i);
 return result;
}
std::string sitrepQuote(const std::string &s)
{
 std::string out="\"";
 for(unsigned char c:s) { if(c=='"'||c=='\\') {out+='\\';out+=c;} else if(c=='\n')out+="\\n"; else if(c=='\r')out+="\\r"; else if(c=='\t')out+="\\t"; else if(c>=32)out+=c; }
 return out+"\"";
}
std::string sitrepIds(const std::vector<int> &ids)
{
 std::string out="["; for(size_t i=0;i<ids.size();++i) {if(i)out+=",";out+=std::to_string(ids[i]);}return out+"]";
}
struct SitrepGroup { std::set<int> identities; std::vector<int> receipts; };
void addSitrep(SitrepGroup &g,int identity,int receipt)
{
 if(g.identities.insert(identity).second && g.receipts.size()<8)g.receipts.push_back(receipt);
}
std::string sitrepGroups(const std::map<std::string,SitrepGroup> &groups,const std::string &key)
{
 std::string out="[";int n=0;
 for(const auto &p:groups) {if(n++)out+=",";out+="{"+sitrepQuote(key)+":"+sitrepQuote(p.first)+",\"count\":"+std::to_string(p.second.identities.size())+",\"evidenceIds\":"+sitrepIds(p.second.receipts)+"}";}
 return out+"]";
}
}
namespace
{
std::string operationalReview(const SavedGame &save,const std::string &period,const std::set<int> &unavailable)

{
 const auto &audit=save.getAlienCommand().getAudit();
 std::map<int,const AlienMission*> active;
 for(const auto *m:save.getAlienMissions())active[m->getId()]=m;
 struct CraftRole {std::string type,role,source;int receipt;};
 std::map<int,CraftRole> craftRoles;
 std::map<int,std::vector<std::pair<int,int>>> deployments;
 std::set<int> assigned;
 std::string history;
 for(const auto &raw:audit)
 {
  YAML::YamlRootNodeReader r(YAML::YamlString(raw),"operational review");
  const auto kind=r["kind"].readVal<std::string>();
  if(kind=="own_operation")
  {
   const auto action=r["event"].readVal<std::string>();const int mid=r["missionId"].readVal<int>();
   if(action=="MISSION_ASSIGNED")assigned.insert(mid);
   if(action=="CRAFT_DEPLOYED")
   {
    const int uid=r["sourceUfoId"].readVal<int>(),id=r["id"].readVal<int>();
    deployments[mid].push_back({uid,id});
    std::string type="UNKNOWN",role="UNKNOWN";r.tryRead("craftType",type);r.tryRead("role",role);
    if(type!="UNKNOWN")craftRoles[uid]={type,role,"EXPLICIT_NATIVE_TELEMETRY",id};
   }
  }
  if(kind=="portfolio" && r["input"]["sitrep"])
  {
   auto prior=r["input"]["sitrep"];const auto p=prior["period"].readVal<std::string>();
   if(p<period)
   {
    int activities=0;for(const auto &g:prior["verifiedActivities"].children())activities+=g["count"].readVal<int>();
    history="["+sitrepQuote(p)+","+std::to_string(prior["assets"]["unavailable"].readVal<int>())+","+std::to_string(activities)+"]";
   }
  }
 }
 // Legacy role reconstruction is admitted only for continuously observed own
 // assignments whose complete deployment count agrees with native wave progress.
 for(const auto &pair:deployments)
 {
  auto found=active.find(pair.first);if(!assigned.count(pair.first)||found==active.end())continue;
  const auto *mission=found->second;const auto &rule=mission->getRules();
  size_t expected=mission->getNextUfoCounter();
  for(size_t w=0;w<std::min(mission->getNextWave(),rule.getWaveCount());++w)expected+=rule.getWave(w).ufoCount;
  if(expected!=pair.second.size())continue;
  size_t index=0;
  for(size_t w=0;w<rule.getWaveCount();++w)
   for(size_t c=0;c<rule.getWave(w).ufoCount && index<pair.second.size();++c,++index)
   {
    const auto &d=pair.second[index];if(craftRoles.count(d.first))continue;
    const auto &wave=rule.getWave(w);
    craftRoles[d.first]={wave.ufoType,rule.getObjective()==OBJECTIVE_RETALIATION?"SEARCH":wave.objective?"OBJECTIVE_CARRIER":rule.getObjective()==OBJECTIVE_SITE?"PREPARATION":"UNKNOWN","LEGACY_OWN_SEQUENCE_MATCHED_TO_RULES",d.second};
   }
 }
 std::map<std::string,int> losses{{"PREPARATION",0},{"SEARCH",0},{"OBJECTIVE_CARRIER",0},{"UNKNOWN",0}};
 const int lossCount=(int)unavailable.size();
 std::set<int> seen;std::set<std::pair<std::string,int>> activitiesSeen;std::string support="[";int rows=0,verified=0;
 for(const auto &raw:audit)
 {
  YAML::YamlRootNodeReader r(YAML::YamlString(raw),"role loss review");
  if(r["kind"].readVal<std::string>()=="budget_fact")
  {
   const auto event=r["event"].readVal<std::string>();
   if((event=="RESEARCH_FLIGHT_COMPLETED" || event=="PRODUCTIVE_ACTIVITY_COMPLETED") && activitiesSeen.emplace(event,r["missionId"].readVal<int>()).second && r["gameTime"].readVal<std::string>().substr(0,7)==period)++verified;
  }
  if(r["kind"].readVal<std::string>()!="own_operation" || r["event"].readVal<std::string>()!="CRAFT_UNAVAILABLE")continue;
  const int uid=r["sourceUfoId"].readVal<int>();
  if(!unavailable.count(uid) || !seen.insert(uid).second || r["gameTime"].readVal<std::string>().substr(0,7)!=period)continue;
  auto found=craftRoles.find(uid);std::string role=found==craftRoles.end()?"UNKNOWN":found->second.role;
  if(!losses.count(role))role="UNKNOWN";++losses[role];
  if(rows<16)
  {
   if(rows++)support+=",";
   support+="{\"lossReceiptId\":"+std::to_string(r["id"].readVal<int>())+",\"role\":"+sitrepQuote(role)
    +",\"craftType\":"+sitrepQuote(found==craftRoles.end()?"UNKNOWN":found->second.type)
    +",\"source\":"+sitrepQuote(found==craftRoles.end()?"UNKNOWN":found->second.source)+"}";
  }
 }
 int accounted=0;for(const auto &p:losses)accounted+=p.second;
 losses["UNKNOWN"]+=std::max(0,lossCount-accounted);
 int objectives=0;std::string progress="[";int count=0;
 for(const auto *m:save.getAlienMissions())if(!m->isOver())
 {
  const auto &rule=m->getRules();bool pending=false;
  for(size_t w=m->getNextWave();w<rule.getWaveCount();++w)if(rule.getWave(w).objective)pending=true;
  if(pending && (rule.getType()=="STR_ALIEN_TERROR" || rule.getType()=="STR_ALIEN_SURFACE_ATTACK"))++objectives;
  if(count<16)
  {
   if(count++)progress+=",";
   progress+="{\"missionId\":"+std::to_string(m->getId())+",\"nextWave\":"+std::to_string(m->getNextWave())+",\"totalWaves\":"+std::to_string(rule.getWaveCount())+",\"objectiveWavePending\":"+(pending?"true":"false")+"}";
  }
 }
 std::string roles="{";int n=0;for(const auto &p:losses){if(n++)roles+=",";roles+=sitrepQuote(p.first)+":"+std::to_string(p.second);}
 return "{\"loss_roles\":"+roles+"},\"terror_objective_waves_pending\":"+std::to_string(objectives)
  +",\"rolling_results\":["+(history.empty()?"":history+",")+"["+sitrepQuote(period)+","+std::to_string(lossCount)+","+std::to_string(verified)+"]]"
  +",\"limits\":\"Partial own telemetry. Pending objective is not success; scout loss is not mission failure.\",\"roleSupport\":"+support+"]"
  +",\"pendingProgress\":"+progress+"]}";
}
}
std::string buildAlienMonthlySitrep(const SavedGame &save,const std::string &asOf)
{
 const auto now=asOf.empty()?save.getTime()->getFullString():asOf;
 int year=std::stoi(now.substr(0,4)),month=std::stoi(now.substr(5,2));
 if(--month==0) {month=12;--year;}
 const auto period=std::to_string(year)+"-"+(month<10?"0":"")+std::to_string(month);
 const auto &ledger=save.getAlienCommand();
 std::map<int,std::string> assignments;
 for(const auto *m:save.getAlienMissions())assignments[m->getId()]=m->getRegion();
 for(const auto &event:ledger.getAudit())
 {
  YAML::YamlRootNodeReader r(YAML::YamlString(event),"sitrep assignment");
  const auto kind=r["kind"].readVal<std::string>();
  if(kind=="own_operation")assignments[r["missionId"].readVal<int>()]=r["assignedRegion"].readVal<std::string>();
  if(kind=="decision" && r["execution"]["status"].readVal<std::string>()=="MISSION_CREATED")
   assignments[r["execution"]["missionId"].readVal<int>()]=r["execution"]["region"].readVal<std::string>();
 }
 std::set<int> deployed,returned,unavailable,seenUnavailable;
 std::set<std::pair<std::string,int>> seenActivities;
 std::map<std::string,SitrepGroup> losses,contacts,activities;
 std::string previousStrategy="UNSPECIFIED",previousPortfolio="[]"; int previousReceipt=0;
 for(const auto &event:ledger.getAudit())
 {
  YAML::YamlRootNodeReader r(YAML::YamlString(event),"sitrep event");
  const auto kind=r["kind"].readVal<std::string>();
  const bool inPeriod=r["gameTime"] && r["gameTime"].readVal<std::string>().substr(0,7)==period;
  const int receipt=r["id"].readVal<int>();
  int unavailableId=0,missionId=0;
  if(kind=="own_operation")
  {
   const auto action=r["event"].readVal<std::string>();
   const int craft=r["sourceUfoId"].readVal<int>();
   if(inPeriod && action=="CRAFT_DEPLOYED")deployed.insert(craft);
   if(inPeriod && action=="CRAFT_RETURNED")returned.insert(craft);
   if(action=="CRAFT_UNAVAILABLE") {unavailableId=craft;missionId=r["missionId"].readVal<int>();}
  }
  if(kind=="interception")
  {
   const auto admission=r["admission"].readVal<std::string>();
   if(admission=="REPORTER_LOST") {unavailableId=r["debugOutcome"]["sourceUfoId"].readVal<int>();missionId=r["debugOutcome"]["sourceMissionId"].readVal<int>();}
   if(inPeriod && admission=="ADMITTED")addSitrep(contacts[r["evidence"]["region"].readVal<std::string>()],r["evidence"]["sourceUfoId"].readVal<int>(),receipt);
  }
  if(unavailableId>0 && seenUnavailable.insert(unavailableId).second && inPeriod)
  {
   unavailable.insert(unavailableId);
   const auto a=assignments.find(missionId);
   addSitrep(losses[a==assignments.end()?"ASSIGNMENT_UNKNOWN":a->second],unavailableId,receipt);
  }
  if(kind=="budget_fact")
  {
   const auto action=r["event"].readVal<std::string>();
   if(action=="RESEARCH_FLIGHT_COMPLETED" || action=="PRODUCTIVE_ACTIVITY_COMPLETED")
   {
    const int id=r["missionId"].readVal<int>();
    if(seenActivities.emplace(action,id).second && inPeriod)addSitrep(activities[r["mission"].readVal<std::string>()],id,receipt);
   }
  }
  if(kind=="portfolio" && inPeriod)
  {
   previousReceipt=receipt;previousStrategy="UNSPECIFIED";previousPortfolio="[]";
   const auto status=r["status"].readVal<std::string>();
   if(status=="SAVED_RESOURCES" || status=="PORTFOLIO_EXECUTED")
   {
    const auto raw=r["response"].readVal<std::string>();
    YAML::YamlRootNodeReader model(YAML::YamlString(raw),"prior strategy");
    model.tryRead("strategy",previousStrategy);
    if(status=="PORTFOLIO_EXECUTED")
    {
     int n=0;previousPortfolio="[";
     for(const auto &op:model["operations"].children())
     {if(n++)previousPortfolio+=",";previousPortfolio+="{\"mission\":"+sitrepQuote(op["mission"].readVal<std::string>())+",\"region\":"+sitrepQuote(op["region"].readVal<std::string>())+"}";}
     previousPortfolio+="]";
    }
   }
  }
 }
 std::string pending="[";int n=0,total=0;
 for(const auto *m:save.getAlienMissions())if(!m->isOver())
 {
  ++total;if(n>=16)continue;if(n++)pending+=",";
  pending+="{\"missionId\":"+std::to_string(m->getId())+",\"mission\":"+sitrepQuote(m->getRules().getType())+",\"region\":"+sitrepQuote(m->getRegion())+"}";
 }
 pending+="]";
 return "{\"schemaVersion\":1,\"period\":"+sitrepQuote(period)+",\"coverage\":\"PARTIAL_FLEET_OUTCOMES\",\"previousStrategy\":"+sitrepQuote(previousStrategy)
 +",\"previousPortfolio\":"+previousPortfolio+",\"previousReceiptId\":"+std::to_string(previousReceipt)
 +",\"assets\":{\"deployed\":"+std::to_string(deployed.size())+",\"returned\":"+std::to_string(returned.size())+",\"unavailable\":"+std::to_string(unavailable.size())+"}"
 +",\"lossAssignments\":"+sitrepGroups(losses,"region")+",\"contacts\":"+sitrepGroups(contacts,"region")+",\"verifiedActivities\":"+sitrepGroups(activities,"mission")
 +",\"pendingOperations\":"+pending+",\"pendingTotal\":"+std::to_string(total)+",\"pendingTruncated\":"+(total>16?"true":"false")
 +",\"operationalReview\":"+operationalReview(save,period,unavailable)+",\"enemyRecovery\":\"UNKNOWN\",\"missionSuccess\":\"NOT_INFERRED_FROM_ACTIVITY_OR_DISAPPEARANCE\"}";
}

std::vector<AlienReconCandidate> buildAlienPortfolioMenu(const Mod &mod, const SavedGame &save)
{
 std::vector<AlienReconCandidate> result;
 std::set<std::pair<std::string,std::string>> operationalRegions;
 for (const auto &mission : {"STR_ALIEN_RESEARCH","STR_ALIEN_PROBE_MISSION","STR_ALIEN_HARVEST","STR_ALIEN_ABDUCTION","STR_ALIEN_TERROR","STR_ALIEN_SURFACE_ATTACK","STR_ALIEN_RETALIATION","STR_ALIEN_BASE","STR_ALIEN_INFILTRATION"})
 {
  const auto *rule=mod.getAlienMission(mission);
  if ((std::string(mission)=="STR_ALIEN_BASE" || std::string(mission)=="STR_ALIEN_INFILTRATION") && !save.getAlienCommand().canFund(mission)) continue;
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
   if (rule->getObjective()==OBJECTIVE_SITE && portfolioSiteAreas(*rule,*geo).empty()) valid=false;
   for (const auto *existing:save.getAlienMissions())
    if (existing->getRules().getType()==mission && existing->getRegion()==geo->getType()) valid=false;
   if (valid && operationalRegions.emplace(mission,geo->getType()).second) result.push_back({mission,name});
  }
 }
 return result;
}
std::string buildAlienPortfolioInput(const Mod &mod, const SavedGame &save)
{
 std::vector<AlienReconCandidate> regions;
 for (const auto &region:mod.getRegionsList()) regions.push_back({"REGION",region});
 auto input=save.getAlienCommand().snapshot(regions);
 input.candidates=buildAlienPortfolioMenu(mod,save);
 return "{\"schemaVersion\":1,\"budget\":"+save.getAlienCommand().budgetJson()+",\"knowledge\":"+AlienCommand::inputJson(input)+",\"sitrep\":"+buildAlienMonthlySitrep(save)+"}";
}
void executeAlienPortfolio(Game &game, const Globe &globe)
{
 auto &save=*game.getSavedGame(); auto &ledger=save.getAlienCommand(); auto &mod=*game.getMod();
 ledger.beginBudgetMonth(std::max(0,save.getMonthsPassed()),(int)save.getDifficulty());
 if (!ledger.portfolioDue()) return;
 auto menu=buildAlienPortfolioMenu(mod,save);
 const auto body=buildAlienPortfolioInput(mod,save);
 auto response=queryAlienPortfolioModel(body,Options::alienCommandModelPort);
 std::string status="MODEL_UNAVAILABLE_SAVE_RESOURCES";
 std::vector<AlienReconCandidate> selected;
 try
 {
  YAML::YamlRootNodeReader r(YAML::YamlString(response),"alien portfolio response");
  if (r["schemaVersion"].readVal<int>()!=1 || r["protocol"].readVal<std::string>()!="alien-strategy-laya-v2"
    || r["checkpointSha256"].readVal<std::string>()!="bcbb891d21cf081a9d7a941b97f8b0f10cf3dac7473b4b9450fab0d07b885175") throw std::runtime_error("Portfolio identity mismatch");
  const auto strategy=r["strategy"].readVal<std::string>();
  if (strategy!="RESOURCE_ACQUISITION" && strategy!="POLITICAL_PRESSURE" && strategy!="INTELLIGENCE" && strategy!="COUNTER_XCOM" && strategy!="NO_FEASIBLE_OPERATION") throw std::runtime_error("Invalid strategy");
  if(strategy=="NO_FEASIBLE_OPERATION" && std::any_of(menu.begin(),menu.end(),[&](const auto &m){return ledger.canFund(m.mission);})) throw std::runtime_error("Feasible strategy incorrectly omitted");
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
    const auto areas=portfolioSiteAreas(*rule,*mod.getRegion(mission->getRegion()));
    mission->setMissionSiteZoneArea(areas.at(RNG::generate(0,areas.size()-1)));
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
