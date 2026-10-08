// SPDX-License-Identifier: GPL-3.0-or-later

#include "../src/Savegame/AlienCommand.h"
#include "../src/Geoscape/AlienCommandAudit.h"
#include "../src/Geoscape/AlienCommandModel.h"
#include "../src/Savegame/GameTime.h"
#include "../src/Menu/SaveGameState.h"
#include "../src/Geoscape/DogfightState.h"
#include "../src/Geoscape/GeoscapeState.h"
#include "../src/Engine/CrossPlatform.h"
#include "../src/Engine/Game.h"
#include "../src/Engine/Options.h"
#include "../src/Engine/RNG.h"
#include "../src/Engine/State.h"
#include "../src/Engine/Screen.h"
#include "../src/Engine/Palette.h"
#include "../src/Engine/Yaml.h"
#include "../src/Mod/Mod.h"
#include "../src/Mod/RuleCraft.h"
#include "../src/Mod/RuleMissionScript.h"
#include "../src/Mod/RuleAlienMission.h"
#include "../src/Mod/UfoTrajectory.h"
#include "../src/Mod/RuleRegion.h"
#include "../src/Savegame/AlienMission.h"
#include "../src/Savegame/AlienStrategy.h"
#include "../src/Savegame/Base.h"
#include "../src/Savegame/Craft.h"
#include "../src/Savegame/SavedGame.h"
#include "../src/Savegame/Ufo.h"
#include <iostream>
#include <algorithm>
#include <cstdlib>
#include <limits>
#include <sstream>
#include <stdexcept>
#ifdef main
#undef main
#endif
using namespace OpenXcom;
static int checks = 0;
void check(bool condition, const char *message)
{
	if (!condition) throw std::runtime_error(message);
	++checks;
}
std::string readText(const std::string &path)
{
	auto stream = CrossPlatform::readFile(path);
	if (!stream) throw std::runtime_error("Cannot read " + path);
	std::ostringstream out; out << stream->rdbuf(); return out.str();
}
AlienInterceptionContact contact(int ufo, const std::string &region, const std::string &time = "1999-01-01 12:00:00")
{
	AlienInterceptionContact c;
	c.observed = true; c.ufoId = ufo; c.missionId = 7;
	c.region = region; c.observedAt = time; c.longitude = 1.2; c.latitude = 0.4;
	return c;
}
std::string serialize(const AlienCommand &command)
{
	YAML::YamlRootNodeWriter w; w.setAsMap(); command.save(w["alienCommand"]); return w.emit().yaml;
}
std::string latestBudgetFact(const AlienCommand &command)
{
 for(auto it=command.getAudit().rbegin();it!=command.getAudit().rend();++it)
 {YAML::YamlRootNodeReader r(YAML::YamlString(*it),"budget fact lookup");if(r["kind"].readVal<std::string>()=="budget_fact")return *it;}
 throw std::runtime_error("Missing budget fact");
}

void coreTests()
{
 for(int month=0;month<24;++month)
  check(AlienCommand::operationCapacity(month)==3+std::min(3,month/3),"Progressive operation capacity wrong");
	AlienCommand command;
	std::vector<AlienReconCandidate> menu = {{"RECON", "B"}, {"RECON", "A"}};
	check(AlienCommand::chooseRecon(command.snapshot(menu)).abstains(), "No evidence must abstain");
	const auto seed = RNG::getSeed();
	check(!command.reportInterception(contact(1, "A"), "later", false, "UFO_DESTROYED"), "Destroyed UFO cannot report");
	check(command.getEvidence().empty() && command.getBeliefs().empty(), "Lost report leaked into knowledge");
	auto unobserved = contact(2, "A"); unobserved.observed = false;
	check(!command.reportInterception(unobserved, "later", true, "CANCELLED"), "Unobserved contact admitted");
	auto malformed = contact(2, "A"); malformed.latitude = std::numeric_limits<double>::quiet_NaN();
	check(!command.reportInterception(malformed, "later", true, "UFO_SURVIVED"), "Invalid location admitted");
	check(command.reportInterception(contact(3, "A"), "later", true, "UFO_SURVIVED"), "Survivor report rejected");
	check(!command.reportInterception(contact(3, "A"), "later", true, "UFO_SURVIVED"), "Duplicate contact admitted");
	check(command.reportInterception(contact(3, "A", "second contact"), "later", true, "UFO_SURVIVED"), "Second encounter rejected");
	check(command.getBeliefs().at("A").independentSources == 1, "Repeated reporter inflated independent support");
	check(command.reportInterception(contact(4, "B"), "later", true, "UFO_SURVIVED"), "B report rejected");
	check(command.reportInterception(contact(5, "B"), "later", true, "UFO_SURVIVED"), "Independent B report rejected");
	auto snapshot = command.snapshot(menu);
	auto proposed = AlienCommand::chooseRecon(snapshot);
	check(proposed.region == "B" && proposed.mission == "RECON", "Evidence did not steer recon");
	check(AlienCommand::validateProposal(snapshot, proposed), "In-menu proposal failed validation");
	const std::string modelFixture = "{\"schemaVersion\":1,\"status\":\"PREDICTED\",\"checkpointSha256\":\""
		+ std::string(64, 'a') + "\",\"answer\":{\"probabilities\":{\"C0\":0.8,\"C1\":0.2}},"
		"\"proposal\":{\"mission\":\"RECON\",\"region\":\"B\",\"reason\":\"MODEL_PICK\","
		"\"score\":50,\"evidenceIds\":[6,5]}}";
	// Get the actual admitted support rather than depend on fixture event numbering.
	std::string validModel = modelFixture.substr(0, modelFixture.find("\"evidenceIds\""));
	validModel += "\"evidenceIds\":[" + std::to_string(proposed.evidenceIds[0]) + ","
		+ std::to_string(proposed.evidenceIds[1]) + "]}}";
	check(validateAlienReconModelResponse(snapshot, validModel).status == "MODEL_PROPOSAL_VALID_SHADOW_ONLY", "Valid model proposal rejected");
	auto fabricated = validModel;
	const auto regionAt = fabricated.find("\"region\":\"B\"");
	fabricated.replace(regionAt, std::string("\"region\":\"B\"").size(), "\"region\":\"HIDDEN_BASE\"");
	check(validateAlienReconModelResponse(snapshot, fabricated).status == "REJECTED_MODEL_RESPONSE", "Model invented region accepted");
	check(validateAlienReconModelResponse(snapshot, "{bad").status == "REJECTED_MODEL_RESPONSE", "Malformed model response accepted");
	check(queryAlienReconModel(snapshot, -1).status == "INVALID_MODEL_PORT", "Invalid model port accepted");
	check(queryAlienReconModel(AlienReconSnapshot{}, 18867).status == "NO_ADMITTED_EVIDENCE", "No-evidence model guard failed");
	auto invalid = proposed; invalid.region = "HIDDEN_BASE";
	check(!AlienCommand::validateProposal(snapshot, invalid), "Out-of-menu proposal accepted");
	invalid = proposed; invalid.score = 101;
	check(!AlienCommand::validateProposal(snapshot, invalid), "Invalid confidence accepted");
	invalid = proposed; invalid.evidenceIds = {999999};
	check(!AlienCommand::validateProposal(snapshot, invalid), "Invented evidence accepted");
	invalid = proposed; invalid.evidenceIds.push_back(invalid.evidenceIds.front());
	check(!AlienCommand::validateProposal(snapshot, invalid), "Duplicate evidence accepted");
	auto unsupported = snapshot; unsupported.evidence.clear();
	check(AlienCommand::chooseRecon(unsupported).abstains(), "Unproven belief used by policy");
	check(RNG::getSeed() == seed, "Evidence/policy consumed game RNG");
	AlienCommandExecution execution; execution.rngBefore = seed; execution.rngAfter = seed;
	command.recordDecision("now", 4, "recon", "RECON", snapshot, proposed, execution);
	YAML::YamlRootNodeReader receipt(YAML::YamlString(command.getAudit().back()), "receipt");
	check(!receipt["validation"]["executedProposal"].readVal<bool>(), "Shadow proposal marked executed");
	check(receipt["input"]["evidence"].children().size() > 0, "Receipt missing admitted evidence");
	const auto stored = serialize(command);
	YAML::YamlRootNodeReader reader(YAML::YamlString(stored), "roundtrip");
	AlienCommand restored; restored.load(reader["alienCommand"]);
	check(serialize(restored) == stored, "Alien worldview did not roundtrip exactly");
	check(restored.exportJsonl() == command.exportJsonl(), "Audit receipts changed on load");
	auto adjusted = stored;
	const auto confidence = adjusted.find("confidence: 50");
	check(confidence != std::string::npos, "Missing confidence fixture");
	adjusted.replace(confidence, std::string("confidence: 50").size(), "confidence: 77");
	YAML::YamlRootNodeReader adjustedReader(YAML::YamlString(adjusted), "stored belief");
	restored.load(adjustedReader["alienCommand"]);
	check(AlienCommand::chooseRecon(restored.snapshot(menu)).score == 77, "Load silently recomputed beliefs");
	YAML::YamlRootNodeReader legacy(YAML::YamlString("legacy: true\n"), "old save");
	restored.load(legacy["alienCommand"]);
	check(restored.empty(), "Absent old-save field did not restore empty state");
	bool rejected = false;
	try { YAML::YamlRootNodeReader future(YAML::YamlString("schemaVersion: 99\n"), "future"); restored.load(future.toBase()); }
	catch (const YAML::Exception &) { rejected = true; }
	check(rejected, "Unknown save schema silently discarded");
	std::vector<AlienReconCandidate> huge;
	for (size_t i = 0; i <= AlienCommand::MAX_CANDIDATES; ++i) huge.push_back({"RECON", std::to_string(i)});
	check(AlienCommand::chooseRecon(command.snapshot(huge)).reason == "MENU_LIMIT_EXCEEDED", "Unbounded menu accepted");
	check(AlienCommand::chooseRecon(command.snapshot({})).reason == "EMPTY_MENU", "Empty menu did not abstain");
	AlienCommand escapes;
	auto quoted = contact(7, "region \"quoted\"\n"); escapes.reportInterception(quoted, "time", true, "UFO_SURVIVED");
	YAML::YamlRootNodeReader escaped(YAML::YamlString(escapes.getAudit().back()), "escaping");
	check(escaped["evidence"]["region"].readVal<std::string>() == quoted.region, "JSON string escaping broken");
}
void budgetStateTests()
{
 AlienCommand b; b.beginBudgetMonth(1,4);
 check(b.remainingBudget()==11,"Wrong difficulty/month allowance");
 check(!b.canFund("STR_ALIEN_BASE"),"Infrastructure prerequisite bypass");
 check(!b.fundMission(1,"UNKNOWN"),"Unknown operation was free");
 check(b.fundMission(1,"STR_ALIEN_HARVEST"),"Affordable harvest rejected");
 check(b.fundMission(1,"STR_ALIEN_HARVEST") && b.remainingBudget()==8,"Duplicate charge");
 check(!b.fundMission(1,"STR_ALIEN_RESEARCH"),"Commitment identity changed");
 b.recordBudgetFact("PRODUCTIVE_ACTIVITY_COMPLETED",1,"STR_ALIEN_HARVEST","test");
 b.recordBudgetFact("PRODUCTIVE_ACTIVITY_COMPLETED",1,"STR_ALIEN_HARVEST","test");
 auto raw=serialize(b); YAML::YamlRootNodeReader r(YAML::YamlString(raw),"budget save"); AlienCommand loaded; loaded.load(r["alienCommand"]);
 check(loaded.budgetJson()==b.budgetJson(),"Budget/progression did not survive load");
 loaded.beginBudgetMonth(2,4);
 check(loaded.remainingBudget()==19,"Carry or once-only productive bonus wrong");
 loaded.beginBudgetMonth(2,4); check(loaded.remainingBudget()==19,"Reload allocated twice");
 check(loaded.fundMission(2,"STR_ALIEN_HARVEST"),"Second harvest rejected");
 loaded.recordBudgetFact("PRODUCTIVE_ACTIVITY_COMPLETED",2,"STR_ALIEN_HARVEST","test");
 check(loaded.canFund("STR_ALIEN_BASE"),"Verified logistics did not unlock infrastructure");
 check(loaded.fundMission(3,"STR_ALIEN_RETALIATION") && loaded.searchOnly(3),"Search not separated from assault");
 check(AlienCommand::monthlyAllowance(18,4)==48 && AlienCommand::monthlyAllowance(50,4)==48,"Allowance taper changed");
}

SavedGame *newCampaign(Game &game, uint64_t seed)
{
	RNG::setSeed(seed);
	auto *save = game.getMod()->newSave(DIFF_BEGINNER);
	game.setSavedGame(save);
	auto *base = save->getBases()->front();
	base->setName("Audit test base"); base->setLongitude(1.0); base->setLatitude(0.5);
	save->addMonth(); save->addMonth();
	return save;
}
std::string missionSummary(SavedGame &save)
{
	std::string result;
	for (const auto *m : save.getAlienMissions())
		result += m->getRules().getType() + ":" + m->getRegion() + ":" + m->getRace()
			+ ":" + std::to_string(m->getId()) + ":" + std::to_string(m->getWaveCountdown()) + "\n";
	YAML::YamlRootNodeWriter strategy; strategy.setAsMap(); save.getAlienStrategy().save(strategy["strategy"]);
	return result + strategy.emit().yaml + std::to_string(RNG::getSeed());
}
void campaignTests(Game &game)
{
	Options::alienCommandAudit = false;
	auto *save = newCampaign(game, 123456);
	{ GeoscapeState geo; geo.determineAlienMissions(); }
	const auto baseline = missionSummary(*save);
	check(save->getAlienCommand().empty(), "Audit-off campaign recorded events");
	Options::alienCommandAudit = true;
	save = newCampaign(game, 123456);
	{ GeoscapeState geo; geo.determineAlienMissions(); }
	check(missionSummary(*save) == baseline, "Audit changed actual mission selection, strategy, or RNG");
	check(!save->getAlienCommand().getAudit().empty(), "Real scheduler did not emit audit");
	bool reconSeen = false;
	for (const auto &event : save->getAlienCommand().getAudit())
	{
		YAML::YamlRootNodeReader r(YAML::YamlString(event), "scheduler receipt");
		if (r["kind"].readVal<std::string>() == "decision" && r["scope"].readVal<std::string>() == "RECON") reconSeen = true;
	}
	check(reconSeen, "Real reconnaissance opportunity not audited");
	auto menu = buildAlienReconMenu(*game.getMod());
	check(!menu.empty(), "Original-game recon catalog is empty");
	save->getAlienCommand().reportInterception(contact(9001, menu.front().region), "later", true, "UFO_SURVIVED");
	auto *recon = game.getMod()->getMissionScript("recon", true);
	{ AlienCommandMissionAudit audit(&save->getAlienCommand(), *game.getMod(), *recon, "fixed opportunity", 0); }
	const auto first = save->getAlienCommand().getAudit().back();
	save->getBases()->front()->setLongitude(4.0); save->getBases()->front()->setLatitude(-0.8); save->setFunds(999999999);
	{ AlienCommandMissionAudit audit(&save->getAlienCommand(), *game.getMod(), *recon, "fixed opportunity", 0); }
	YAML::YamlRootNodeReader a(YAML::YamlString(first), "before hidden change");
	YAML::YamlRootNodeReader b(YAML::YamlString(save->getAlienCommand().getAudit().back()), "after hidden change");
	check(a["input"].emit().yaml == b["input"].emit().yaml, "Hidden base/funds changed policy input");
	check(a["proposal"].emit().yaml == b["proposal"].emit().yaml, "Hidden base/funds changed shadow decision");
	if (Options::alienCommandModelPort != 0)
	{
		const auto status = a["model"]["status"].readVal<std::string>();
		check(status == "MODEL_PROPOSAL_VALID_SHADOW_ONLY" || status == "MODEL_ABSTAIN",
			"Actual Geoscape hook did not obtain a valid real model response");
		YAML::YamlRootNodeReader beforeModel(YAML::YamlString(a["model"]["rawResponse"].readVal<std::string>()), "model before hidden change");
		YAML::YamlRootNodeReader afterModel(YAML::YamlString(b["model"]["rawResponse"].readVal<std::string>()), "model after hidden change");
		check(beforeModel["state"].emit().yaml == afterModel["state"].emit().yaml
			&& beforeModel["answer"].emit().yaml == afterModel["answer"].emit().yaml,
			"Hidden base/funds changed actual model input or answer");
	}
	save->save("audit-fixture.sav", game.getMod());
	const auto expected = serialize(save->getAlienCommand());
	SavedGame loaded; loaded.load("audit-fixture.sav", game.getMod(), game.getLanguage());
	check(serialize(loaded.getAlienCommand()) == expected, "Real SavedGame save/load changed alien knowledge");
	check(readText(Options::getMasterUserFolder() + "audit-fixture.sav.alien-command.jsonl")
		== save->getAlienCommand().exportJsonl(), "Save sidecar differs from authoritative audit");
	const auto raw = readText(Options::getMasterUserFolder() + "audit-fixture.sav");
	const auto bodyStart = raw.find("---\n");
	check(bodyStart != std::string::npos, "Save body marker not found");
	const auto body = raw.substr(bodyStart + 4);
	auto tree = ryml::parse_in_arena(ryml::to_csubstr(body));
	tree.rootref().remove_child("alienCommand");
	const auto legacyBody = ryml::emitrs_yaml<std::string>(tree);
	check(CrossPlatform::writeFile(Options::getMasterUserFolder() + "legacy-fixture.sav",
		raw.substr(0, bodyStart + 4) + legacyBody), "Could not save legacy fixture");
	loaded.load("legacy-fixture.sav", game.getMod(), game.getLanguage());
	check(loaded.getAlienCommand().empty(), "Real legacy save fabricated alien knowledge");
	// Exercise the actual UI save path, which writes .bak and promotes the save.
	auto *saveState = new SaveGameState(OPT_GEOSCAPE, SAVE_QUICK,
		game.getMod()->getPalette("PAL_GEOSCAPE")->getColors());
	game.pushState(saveState);
	for (int i = 0; i < 11; ++i) saveState->think();
	const auto quickPath = Options::getMasterUserFolder() + SavedGame::QUICKSAVE;
	check(CrossPlatform::fileExists(quickPath), "Actual UI save did not finalize");
	check(readText(quickPath + ".alien-command.jsonl") == save->getAlienCommand().exportJsonl(),
		"Actual UI save did not promote its audit sidecar");
	check(!CrossPlatform::fileExists(quickPath + ".bak.alien-command.jsonl"),
		"Actual UI save left a temporary audit sidecar");
}
void operationalTests(Game &game)
{
 const char *fixture = std::getenv("OPENXCOM_OPERATION_FIXTURE");
 if (!fixture) return;
 Options::alienCommandAudit = true;
 Options::alienCommandModelExecute = true;
 auto *save = newCampaign(game, 654321);
 const auto menu = buildAlienReconMenu(*game.getMod());
 save->getAlienCommand().reportInterception(contact(9100, menu.front().region), "fixture time", true, "UFO_SURVIVED");
 { GeoscapeState geo; geo.determineAlienMissions(); }
 bool reconSeen = false;
 const auto decisions = save->getAlienCommand().getAudit();
 for (const auto &event : decisions)
 {
  YAML::YamlRootNodeReader r(YAML::YamlString(event), "operational receipt");
  if (r["kind"].readVal<std::string>() != "decision" || r["script"].readVal<std::string>() != "recon") continue;
  reconSeen = true;
  const std::string mode(fixture);
  const bool shouldExecute = mode == "research" || mode == "base";
  check(r["model"]["executedProposal"].readVal<bool>() == shouldExecute, "Operational execution/fallback mismatch");
  check(r["execution"]["source"].readVal<std::string>() == (shouldExecute ? "MODEL_COMMANDER" : "LEGACY_COMMANDER"), "Wrong operational commander");
  if (shouldExecute)
  {
   const auto expected = mode == "base" ? "STR_ALIEN_RETALIATION" : menu.front().mission.c_str();
   check(r["execution"]["mission"].readVal<std::string>() == expected, "Model intent did not become engine operation");
   check(r["execution"]["region"].readVal<std::string>() == r["model"]["proposal"]["region"].readVal<std::string>(), "Model region did not execute");
   check(r["mode"].readVal<std::string>() == "MODEL_EXECUTION", "Execution labelled shadow");
   // Advance the actual mission timer to spawn the first wave; no fabricated UFO.
   AlienMission *selected = nullptr;
   for (auto *mission : save->getAlienMissions()) if (mission->getId() == r["execution"]["missionId"].readVal<int>()) selected = mission;
   check(selected != nullptr, "Receipt does not identify a real engine mission");
   GeoscapeState geo;
   bool spawned = false;
   for (int tick = 0; tick < 800 && !spawned; ++tick)
   {
    geo.time30Minutes();
    for (const auto *ufo : *save->getUfos()) if (ufo->getMission() == selected) spawned = true;
   }
   check(spawned, "Selected operation spawned no UFO wave");
   Ufo *observer = nullptr;
   for (auto *ufo : *save->getUfos()) if (ufo->getMission() == selected) observer = ufo;
   auto *base = save->getBases()->front();
   observer->setLongitude(base->getLongitude()); observer->setLatitude(base->getLatitude());
   observer->setTrajectoryPoint(2);
   Options::aggressiveRetaliation = false;
   for (int tick = 0; tick < 1000 && !base->getRetaliationTarget(); ++tick) geo.time10Minutes();
   check(base->getRetaliationTarget() == (mode == "base"), "Research/search base discovery capabilities mismatch");
   if (mode == "base")
   {
    bool discoverySeen = false;
    for (const auto &entry : save->getAlienCommand().getAudit())
    { YAML::YamlRootNodeReader discovery(YAML::YamlString(entry), "discovery receipt");
      if (discovery["kind"].readVal<std::string>() == "base_discovery") discoverySeen = true; }
    check(discoverySeen, "Engine base discovery not audited");
   }
  }
 }
 check(reconSeen, "Operational scheduler did not reach recon opportunity");
 if (std::string(fixture) == "research" || std::string(fixture) == "base")
 {
  { GeoscapeState geo; geo.determineAlienMissions(); }
  bool duplicateFallback = false;
  for (const auto &event : save->getAlienCommand().getAudit())
  {
   YAML::YamlRootNodeReader r(YAML::YamlString(event), "duplicate receipt");
   if (r["kind"].readVal<std::string>() == "decision" && r["script"].readVal<std::string>() == "recon"
    && r["execution"]["operationalStatus"].readVal<std::string>() == "FALLBACK_DUPLICATE_ACTIVE_MISSION") duplicateFallback = true;
  }
  check(duplicateFallback, "Duplicate active operation did not fall back");
 }
 else
 {
  const auto actual = missionSummary(*save);
  Options::alienCommandModelExecute = false;
  const int port = Options::alienCommandModelPort; Options::alienCommandModelPort = 0;
  save = newCampaign(game, 654321);
  save->getAlienCommand().reportInterception(contact(9100, menu.front().region), "fixture time", true, "UFO_SURVIVED");
  { GeoscapeState geo; geo.determineAlienMissions(); }
  check(missionSummary(*save) == actual, "Fallback changed legacy missions, strategy, or RNG");
  Options::alienCommandModelPort = port;
 }
 Options::alienCommandModelExecute = false;
}

void portfolioTests(Game &game)
{
 const char *mode=std::getenv("OPENXCOM_PORTFOLIO_FIXTURE"); if (!mode) return;
 Options::alienCommandPortfolio=true; Options::alienCommandAudit=true;
 auto *save=newCampaign(game,20261006); GeoscapeState geo;
 const auto menu=buildAlienPortfolioMenu(*game.getMod(),*save);
 check(!menu.empty(),"No executable portfolio menu");
 std::set<std::string> types; for (const auto &c:menu) types.insert(c.mission);
 check(types.count("STR_ALIEN_RETALIATION")!=0,"Search missing from portfolio");
 check(types.size()>=3,"Portfolio lacks competing objectives");
 if(Options::getActiveMaster()=="xcom1") check(std::none_of(menu.begin(),menu.end(),[](const auto &c){return c.mission=="STR_ALIEN_TERROR" && (c.region=="STR_ARCTIC" || c.region=="STR_ANTARCTIC");}),"Terror menu admitted non-site polar areas");
 geo.determineAlienMissions();
 const bool valid=std::string(mode)=="valid";
 const bool real=std::string(mode)=="real";
 check(real ? save->getAlienMissions().size()<=3 : save->getAlienMissions().size()==(valid?3:0),"Portfolio did not replace stock scheduler or reject atomically");
 auto balance=save->getAlienCommand().remainingBudget();
 check(real ? balance>=0 && balance<=6 : balance==(valid?0:6),"Portfolio charged incorrect total");
 if (real)
 {
  const auto &receipt=save->getAlienCommand().getAudit().back();
  YAML::YamlRootNodeReader r(YAML::YamlString(receipt),"real portfolio");
  const auto status=r["status"].readVal<std::string>();
  check(status=="SAVED_RESOURCES" || status=="PORTFOLIO_EXECUTED","Real checkpoint portfolio unavailable/rejected");
 }
 auto count=save->getAlienMissions().size(); geo.determineAlienMissions();
 if(valid || real)
 {
  for(const auto *mission:save->getAlienMissions())
  {
   if(mission->getRules().getType()!="STR_ALIEN_RETALIATION")continue;
   if(Options::getActiveMaster()=="xcom1")
    check(mission->getRace()=="STR_SECTOID" || mission->getRace()=="STR_FLOATER" || mission->getRace()=="STR_SNAKEMAN","Independent early search used unrestricted retaliation race");
   else
    check(mission->getRace()=="STR_AQUATOID" || mission->getRace()=="STR_GILLMAN" || mission->getRace()=="STR_LOBSTERMAN","Independent early underwater search used unrestricted retaliation race");
  }
 }
 check(CrossPlatform::writeFile(Options::getMasterUserFolder()+"portfolio-audit.jsonl",save->getAlienCommand().exportJsonl()),"Cannot export portfolio test receipt");
 check(save->getAlienMissions().size()==count && save->getAlienCommand().remainingBudget()==balance,"Same month scheduled/allocated twice");
 auto raw=serialize(save->getAlienCommand()); YAML::YamlRootNodeReader r(YAML::YamlString(raw),"portfolio persistence"); AlienCommand restored; restored.load(r["alienCommand"]);
 check(!restored.portfolioDue(),"Reload repeated portfolio");
 save->save("portfolio-fixture.sav",game.getMod()); SavedGame loaded;
 loaded.load("portfolio-fixture.sav",game.getMod(),game.getLanguage());
 check(serialize(loaded.getAlienCommand())==serialize(save->getAlienCommand()),"Real campaign save changed budget/portfolio state");
 if (valid || std::string(mode)=="save")
 {
  const auto next=buildAlienMonthlySitrep(loaded,std::to_string(loaded.getTime()->getYear())+"-02-01 00:00:00");
  YAML::YamlRootNodeReader s(YAML::YamlString(next),"prior portfolio review");
  check(s["previousStrategy"].readVal<std::string>()=="INTELLIGENCE","Reload lost previous strategy");
  check(s["previousPortfolio"].children().size()==(valid?3:0),"Prior portfolio review invented/lost commitments");
 }
 // Common start checks apply even outside the monthly commander.
 const auto &c=menu.front(); AlienMission unfunded(*game.getMod()->getAlienMission(c.mission));
 unfunded.setId(99901); unfunded.setRegion(c.region,*game.getMod()); unfunded.setRace(game.getMod()->getAlienRacesList().front());
 if (valid) { unfunded.start(game,*geo.getGlobe()); check(unfunded.isOver(),"Out-of-budget external start bypassed gate"); }
 if (valid)
 {
  bool spawn=false; for(int tick=0;tick<800 && !spawn;++tick) {geo.time30Minutes();spawn=!save->getUfos()->empty();}
  check(spawn,"Portfolio created no actual UFO wave");
 }
 Options::alienCommandPortfolio=false;
}

void sitrepTests(Game &game)
{
 auto *save=newCampaign(game,884422);auto &ledger=save->getAlienCommand();
 const auto region=buildAlienReconMenu(*game.getMod()).front().region;
 ledger.recordOwnedOperation("MISSION_ASSIGNED",9900,"STR_ALIEN_RESEARCH",region,"1999-01-01 00:00:00");
 ledger.recordOwnedOperation("CRAFT_DEPLOYED",9900,"STR_ALIEN_RESEARCH",region,"1999-01-02 00:00:00",9910,"STR_MEDIUM_SCOUT",0,"PREPARATION");
 auto lost=contact(9910,"STR_HIDDEN_ENCOUNTER","1999-01-03 00:00:00");lost.missionId=9900;
 ledger.reportInterception(lost,"1999-01-03 00:00:00",false,"UFO_CRASHED");
 ledger.recordOwnedOperation("CRAFT_UNAVAILABLE",9900,"STR_ALIEN_RESEARCH",region,"1999-01-03 00:00:00",9910);
 ledger.recordBudgetFact("RESEARCH_FLIGHT_COMPLETED",9900,"STR_ALIEN_RESEARCH","1999-01-04 00:00:00",9911);
 ledger.recordBudgetFact("RESEARCH_FLIGHT_COMPLETED",9900,"STR_ALIEN_RESEARCH","1999-01-05 00:00:00",9912);
 auto raw=buildAlienMonthlySitrep(*save,"1999-02-01 00:00:00");
 YAML::YamlRootNodeReader r(YAML::YamlString(raw),"monthly sitrep");
 check(r["assets"]["unavailable"].readVal<int>()==1,"Monthly losses double counted legacy/owned receipts");
 check(r["assets"]["deployed"].readVal<int>()==1,"Owned deployments missing");
 check(r["operationalReview"]["loss_roles"]["PREPARATION"].readVal<int>()==1,"Explicit craft role was lost");
 check(r["operationalReview"]["roleSupport"].children().front()["source"].readVal<std::string>()=="EXPLICIT_NATIVE_TELEMETRY","Explicit role mislabelled as inferred");
 check(r["lossAssignments"].children().front()["region"].readVal<std::string>()==region,"Loss not assigned to owned mission region");
 check(raw.find("STR_HIDDEN_ENCOUNTER")==std::string::npos,"Lost reporter location leaked through sitrep");
 check(r["verifiedActivities"].children().front()["count"].readVal<int>()==1,"Repeated productive flights inflated mission gains");
 check(r["enemyRecovery"].readVal<std::string>()=="UNKNOWN","Enemy capture fabricated");
 auto before=raw;save->getBases()->front()->setLongitude(4.5);save->setFunds(999999999);
 check(buildAlienMonthlySitrep(*save,"1999-02-01 00:00:00")==before,"Hidden base/funds changed sitrep");
 auto feb=buildAlienMonthlySitrep(*save,"1999-03-01 00:00:00");YAML::YamlRootNodeReader next(YAML::YamlString(feb),"next month");
 check(next["assets"]["unavailable"].readVal<int>()==0,"January loss repeated in February");
 check(buildAlienMonthlySitrep(*save,"2000-01-01 00:00:00").find("1999-12")!=std::string::npos,"Sitrep year rollover wrong");
 save->save("sitrep-fixture.sav",game.getMod());SavedGame loaded;loaded.load("sitrep-fixture.sav",game.getMod(),game.getLanguage());
 check(buildAlienMonthlySitrep(loaded,"1999-02-01 00:00:00")==before,"Sitrep changed on campaign save/load");
 ledger.beginBudgetMonth(2,4);
 const auto earlyMenu=buildAlienPortfolioMenu(*game.getMod(),*save);
 check(std::none_of(earlyMenu.begin(),earlyMenu.end(),[](const auto &c){return c.mission=="STR_ALIEN_BASE" || c.mission=="STR_ALIEN_INFILTRATION";}), "Advanced menu bypassed progression");
 for(int id : {9920,9921}) {check(ledger.fundMission(id,"STR_ALIEN_HARVEST"),"Cannot fund progression fixture");ledger.recordBudgetFact("PRODUCTIVE_ACTIVITY_COMPLETED",id,"STR_ALIEN_HARVEST","1999-03-01 00:00:00");}
 check(ledger.fundMission(9922,"STR_ALIEN_RESEARCH"),"Cannot fund intelligence fixture");ledger.recordBudgetFact("RESEARCH_FLIGHT_COMPLETED",9922,"STR_ALIEN_RESEARCH","1999-03-01 00:00:00");
 ledger.beginBudgetMonth(3,4);
 for(int id : {9923,9924}) {check(ledger.fundMission(id,"STR_ALIEN_ABDUCTION"),"Cannot fund adaptation fixture");ledger.recordBudgetFact("PRODUCTIVE_ACTIVITY_COMPLETED",id,"STR_ALIEN_ABDUCTION","1999-04-01 00:00:00");}
 const auto advancedMenu=buildAlienPortfolioMenu(*game.getMod(),*save);
 for(const auto &type : {"STR_ALIEN_BASE","STR_ALIEN_INFILTRATION"})
  if(game.getMod()->getAlienMission(type)) check(std::any_of(advancedMenu.begin(),advancedMenu.end(),[&](const auto &c){return c.mission==type;}),"Earned progression did not unlock advanced menu");
}

void budgetFactTests(Game &game)
{
 auto *save = newCampaign(game, 7788);
 Options::alienCommandAudit = true;
 GeoscapeState geo;
 const auto menu = buildAlienReconMenu(*game.getMod());
 AlienMission research(*game.getMod()->getAlienMission(menu.front().mission, true));
 research.setId(8001); research.setRace(game.getMod()->getAlienRacesList().front());
 research.setRegion(menu.front().region, *game.getMod());
 research.start(game, *geo.getGlobe(), 120);
 YAML::YamlRootNodeReader commitment(YAML::YamlString(latestBudgetFact(save->getAlienCommand())), "budget commitment");
 check(commitment["event"].readVal<std::string>() == "MISSION_COMMITTED", "Common mission start not recorded for budget");
 const auto *trajectory = game.getMod()->getUfoTrajectory("P0", true);
 Ufo returning(game.getMod()->getUfo(game.getMod()->getUfosList().front(), true), 8801);
 returning.setMissionInfo(&research, trajectory);
 returning.setTrajectoryPoint(trajectory->getWaypointCount() - 1);
 research.ufoReachedWaypoint(returning, game, *geo.getGlobe());
 YAML::YamlRootNodeReader completion(YAML::YamlString(latestBudgetFact(save->getAlienCommand())), "research completion");
 check(completion["event"].readVal<std::string>() == "RESEARCH_FLIGHT_COMPLETED", "Completed research flight not recorded");
 check(completion["sourceUfoId"].readVal<int>() == 8801, "Research gain lost UFO provenance");
 for (const auto &name : {"STR_ALIEN_HARVEST", "STR_ALIEN_ABDUCTION"})
 {
  const auto *rules = game.getMod()->getAlienMission(name);
  if (!rules) continue;
  AlienMission productive(*rules); productive.setId(name == std::string("STR_ALIEN_HARVEST") ? 8002 : 8003);
  productive.setRace(game.getMod()->getAlienRacesList().front()); productive.setRegion(menu.front().region, *game.getMod());
  productive.start(game, *geo.getGlobe(), 120);
  Ufo landed(game.getMod()->getUfo(game.getMod()->getUfosList().front(), true), 8802);
  landed.setMissionInfo(&productive, trajectory); landed.setStatus(Ufo::LANDED);
  productive.ufoLifting(landed, *save);
  YAML::YamlRootNodeReader gain(YAML::YamlString(latestBudgetFact(save->getAlienCommand())), "productive completion");
  check(gain["event"].readVal<std::string>() == "PRODUCTIVE_ACTIVITY_COMPLETED", "Productive engine activity not recorded");
  check(gain["mission"].readVal<std::string>() == name, "Productive gain mission type wrong");
 }
 auto *retaliation = new AlienMission(*game.getMod()->getAlienMission("STR_ALIEN_RETALIATION", true));
 retaliation->setId(8004); retaliation->setRace(game.getMod()->getAlienRacesList().front());
 retaliation->setRegion(menu.front().region, *game.getMod());
 retaliation->start(game, *geo.getGlobe(), 30); save->getAlienMissions().push_back(retaliation);
 retaliation->think(game, *geo.getGlobe());
 YAML::YamlRootNodeReader search(YAML::YamlString(latestBudgetFact(save->getAlienCommand())), "search deployment");
 check(search["event"].readVal<std::string>() == "BASE_SEARCH_COMMITTED", "Search deployment not recorded separately");
 auto *base = save->getBases()->front();
 const auto *region = game.getMod()->getRegion(retaliation->getRegion(), true);
 auto location = region->getRandomPoint(2);
 for (int attempt = 0; attempt < 1000 && !region->insideRegion(location.first, location.second); ++attempt) location = region->getRandomPoint(2);
 check(region->insideRegion(location.first, location.second), "Could not place fixture base inside retaliation region");
 base->setLongitude(location.first); base->setLatitude(location.second); base->setRetaliationTarget(true);
 retaliation->setWaveCountdown(30); retaliation->think(game, *geo.getGlobe());
 YAML::YamlRootNodeReader assault(YAML::YamlString(latestBudgetFact(save->getAlienCommand())), "assault deployment");
 check(assault["event"].readVal<std::string>() == "BASE_ASSAULT_COMMITTED", "Assault deployment not recorded separately");
 check(search["sourceUfoId"].readVal<int>() != assault["sourceUfoId"].readVal<int>(), "Search and assault receipts reused UFO identity");
 Options::alienCommandPortfolio=true;
 const auto beforeAssault=save->getUfos()->size();
 retaliation->setWaveCountdown(30); retaliation->think(game,*geo.getGlobe());
 check(save->getUfos()->size()==beforeAssault,"Known base bypassed separate assault commitment");
 YAML::YamlRootNodeReader deferred(YAML::YamlString(latestBudgetFact(save->getAlienCommand())),"deferred assault");
 check(deferred["event"].readVal<std::string>()=="ASSAULT_DEFERRED_SEPARATE_COMMITMENT_REQUIRED","Missing deferred assault receipt");
 Options::alienCommandPortfolio=false;
 save->save("budget-facts-fixture.sav", game.getMod());
 SavedGame loaded; loaded.load("budget-facts-fixture.sav", game.getMod(), game.getLanguage());
 check(serialize(loaded.getAlienCommand()) == serialize(save->getAlienCommand()), "Budget facts changed on save/load");
}

void budgetPersistenceWithoutAuditTests(Game &game)
{
 Options::alienCommandAudit=false;
 auto *save=newCampaign(game,3333);
 auto &ledger=save->getAlienCommand(); ledger.beginBudgetMonth(1,0);
 check(ledger.fundMission(3333,"STR_ALIEN_RESEARCH"),"Native budget without auditing failed");
 check(ledger.empty() && ledger.budgetActive(),"Fixture should isolate budget persistence from audit");
 save->save("budget-without-audit-fixture.sav",game.getMod());
 SavedGame loaded; loaded.load("budget-without-audit-fixture.sav",game.getMod(),game.getLanguage());
 check(loaded.getAlienCommand().budgetActive() && serialize(loaded.getAlienCommand())==serialize(ledger),"Budget disappeared when general audit was disabled");
 Options::alienCommandAudit=true;
}

void dogfightTests(Game &game)
{
	auto *save = newCampaign(game, 321);
	Options::alienCommandAudit = true;
	GeoscapeState geo;
	Craft *craft = nullptr;
	for (auto *c : *save->getBases()->front()->getCrafts())
		if (c->getRules()->getWeapons() > 0) { craft = c; break; }
	check(craft != nullptr, "Original-game interceptor missing");
	const auto menu = buildAlienReconMenu(*game.getMod());
	AlienMission mission(*game.getMod()->getAlienMission(menu.front().mission, true));
	mission.setId(6000); mission.setRace(game.getMod()->getAlienRacesList().front());
	for (int state = 0; state < 4; ++state)
	{
		Ufo ufo(game.getMod()->getUfo(game.getMod()->getUfosList().front(), true), 7000 + state);
		ufo.setId(100 + state); ufo.setLongitude(1.2); ufo.setLatitude(0.4);
		ufo.setMissionInfo(&mission, game.getMod()->getUfoTrajectory("P0", true));
		craft->setStatus("STR_OUT"); craft->setFuel(craft->getFuelMax());
		craft->setLongitude(1.2); craft->setLatitude(0.4); craft->setDestination(&ufo); craft->setInDogfight(true);
		const auto count = save->getAlienCommand().getEvidence().size();
		{
			DogfightState fight(&geo, craft, &ufo, false);
			if (state == 3) { fight.setMinimized(true); fight.setWaitForAltitude(true); }
			fight.update();
			if (state == 1) ufo.setDamage(ufo.getCraftStats().damageMax / 2 + 1, game.getMod());
			if (state == 2) ufo.setDamage(ufo.getCraftStats().damageMax, game.getMod());
			craft->setInDogfight(false); fight.update(); fight.update();
		}
		check(save->getAlienCommand().getEvidence().size() == count + (state == 0 ? 1 : 0),
			"Actual dogfight hook admitted a lost/unobserved report or duplicated a survivor report");
		craft->setDestination(nullptr); craft->setInDogfight(false);
	}
	check(save->getAlienCommand().getEvidence().front().contact.ufoId == 7000, "UFO source identity was not preserved");
}
void replayCampaign(Game &game)
{
	auto *save = new SavedGame();
	game.setSavedGame(save);
	save->load("source.sav", game.getMod(), game.getLanguage());
	if (std::getenv("OPENXCOM_MONTH_TRANSITION"))
	{
		Options::alienCommandPortfolio=true;Options::alienCommandAudit=true;
		GeoscapeState geo;const int month=save->getTime()->getMonth();
		int ticks=0;while(save->getTime()->getMonth()==month && ++ticks<50000)geo.timeAdvance();
		check(save->getTime()->getMonth()!=month,"Copied campaign could not advance to monthly boundary");
		const auto balance=save->getAlienCommand().remainingBudget();const auto audit=save->getAlienCommand().exportJsonl();
		geo.determineAlienMissions();check(save->getAlienCommand().exportJsonl()==audit && save->getAlienCommand().remainingBudget()==balance,"Transition repeated portfolio");
		save->save("transition-result.sav",game.getMod());
		SavedGame restored;restored.load("transition-result.sav",game.getMod(),game.getLanguage());
		check(serialize(restored.getAlienCommand())==serialize(save->getAlienCommand()),"Transition save lost role/portfolio receipts");
		check(!restored.getAlienCommand().portfolioDue(),"Transition reload would repeat March decision");
		check(CrossPlatform::writeFile(Options::getMasterUserFolder()+"transition-audit.jsonl",audit),"Cannot export transition audit");
		std::cout<<"REPLAY: copied campaign crossed month boundary; native portfolio executed; remaining "<<balance<<std::endl;
		return;
	}
	if (std::getenv("OPENXCOM_STRATEGY_REPLAY"))
	{
		const auto seed = RNG::getSeed();
		save->getAlienCommand().beginBudgetMonth(std::max(0, save->getMonthsPassed()), (int)save->getDifficulty());
		const auto body = buildAlienPortfolioInput(*game.getMod(), *save);
		const auto response = queryAlienPortfolioModel(body, Options::alienCommandModelPort);
		check(RNG::getSeed() == seed, "Strategy replay changed RNG");
		check(CrossPlatform::writeFile(Options::getMasterUserFolder() + "strategy-input.json", body), "Cannot export strategy input");
		check(CrossPlatform::writeFile(Options::getMasterUserFolder() + "strategy-response.json", response), "Cannot export strategy response");
		YAML::YamlRootNodeReader r(YAML::YamlString(response), "strategy replay");
		check(r["protocol"].readVal<std::string>() == "alien-strategy-laya-v2", "Strategy replay failed");
		std::cout << "REPLAY: strategy " << r["strategy"].readVal<std::string>() << "; status " << r["status"].readVal<std::string>() << "; no operations executed" << std::endl;
		return;
	}
	const auto original = serialize(save->getAlienCommand());
	const auto input = save->getAlienCommand().snapshot(buildAlienReconMenu(*game.getMod()));
	const auto seed = RNG::getSeed();
	const auto proposal = AlienCommand::chooseRecon(input);
	AlienCommandModelResult model;
	if (Options::alienCommandModelPort != 0)
	{
		model = queryAlienReconModel(input, Options::alienCommandModelPort);
		check(model.status == "MODEL_PROPOSAL_VALID_SHADOW_ONLY" || model.status == "MODEL_ABSTAIN"
			|| model.status == "NO_ADMITTED_EVIDENCE" || model.status == "INPUT_LIMIT",
			"Real model bridge failed or rejected its response");
	}
	check(RNG::getSeed() == seed, "Replay inference changed campaign RNG");
	auto replay = save->getAlienCommand();
	AlienCommandExecution execution;
	execution.source = "OFFLINE_REPLAY";
	execution.status = "NOT_EXECUTED_OFFLINE_REPLAY";
	execution.rngBefore = seed; execution.rngAfter = seed;
	replay.recordDecision(save->getTime()->getFullString(), (int)save->getDifficulty(),
		"recon", "RECON", input, proposal, execution, model);
	check(serialize(save->getAlienCommand()) == original, "Replay changed authoritative alien knowledge");
	const auto path = Options::getMasterUserFolder() + "recon-replay.jsonl";
	check(CrossPlatform::writeFile(path, replay.exportJsonl()), "Cannot export replay");
	std::cout << "REPLAY: baseline " << proposal.mission << " / " << proposal.region
		<< "; model " << model.status << " " << model.proposal.region << "; exported " << path << std::endl;
}
int main(int argc, char *argv[])
{
	try
	{
		const char *replayFlag = std::getenv("OPENXCOM_ALIEN_REPLAY");
		const bool replay = replayFlag && std::string(replayFlag) == "1";
		CrossPlatform::processArgs(argc, argv); YAML::setGlobalErrorHandler();
		if (!Options::init()) throw std::runtime_error("Options initialization failed");
		if (!replay) { coreTests(); budgetStateTests(); }
		Game game("Alien command engine tests"); State::setGamePtr(&game);
		Options::newDisplayWidth = Options::displayWidth; Options::newDisplayHeight = Options::displayHeight;
		Screen::updateScale(Options::geoscapeScale, Options::baseXGeoscape, Options::baseYGeoscape, false);
		Screen::updateScale(Options::battlescapeScale, Options::baseXBattlescape, Options::baseYBattlescape, false);
		Options::baseXResolution = Options::displayWidth; Options::baseYResolution = Options::displayHeight;
		game.getScreen()->resetDisplay(false, true);
		Options::updateMods(); game.loadMods(); game.loadLanguages();
		if (replay) { replayCampaign(game); return 0; }
		const int modelPort = Options::alienCommandModelPort;
		if (std::getenv("OPENXCOM_OPERATION_FIXTURE") || std::getenv("OPENXCOM_PORTFOLIO_FIXTURE")) Options::alienCommandModelPort = 0;
		std::cout << "STAGE campaign" << std::endl; campaignTests(game); std::cout << "STAGE dogfight" << std::endl; dogfightTests(game);
		Options::alienCommandModelPort = modelPort; std::cout << "STAGE operations" << std::endl; operationalTests(game); std::cout << "STAGE budget facts" << std::endl; budgetFactTests(game); budgetPersistenceWithoutAuditTests(game); sitrepTests(game); std::cout << "STAGE portfolio" << std::endl; portfolioTests(game);
		std::cout << "PASS: " << checks << " checks; real engine " << Options::getActiveMaster() << std::endl;
		return 0;
	}
	catch (const std::exception &e) { std::cerr << "FAIL: " << e.what() << std::endl; return 1; }
}
