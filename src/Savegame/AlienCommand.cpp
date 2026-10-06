// SPDX-License-Identifier: GPL-3.0-or-later

#include "AlienCommand.h"
#include "../Engine/Yaml.h"
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <set>
#include <sstream>
#include <tuple>
#include <stdexcept>

namespace OpenXcom
{
namespace
{
std::string quote(const std::string &value)
{
	std::ostringstream out;
	out << '"';
	for (unsigned char c : value)
	{
		switch (c)
		{
		case '"': out << "\\\""; break;
		case '\\': out << "\\\\"; break;
		case '\n': out << "\\n"; break;
		case '\r': out << "\\r"; break;
		case '\t': out << "\\t"; break;
		default:
			if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << (int)c << std::dec;
			else out << c;
		}
	}
	out << '"';
	return out.str();
}
template<typename T, typename F>
std::string array(const std::vector<T> &values, F write)
{
	std::string result = "[";
	for (size_t i = 0; i < values.size(); ++i)
	{
		if (i) result += ",";
		result += write(values[i]);
	}
	return result + "]";
}
std::string ids(const std::vector<int> &values)
{
	return array(values, [](int id) { return std::to_string(id); });
}
bool validContact(const AlienInterceptionContact &c)
{
	return c.observed && c.ufoId > 0 && c.missionId >= 0 && !c.observedAt.empty() && !c.region.empty()
		&& std::isfinite(c.longitude) && std::isfinite(c.latitude)
		&& c.longitude >= 0 && c.longitude <= 6.283185307179586
		&& c.latitude >= -1.570796326794897 && c.latitude <= 1.570796326794897;
}
std::string evidenceJson(const AlienInterceptionEvidence &e)
{
	std::ostringstream out;
	out << std::setprecision(17) << "{\"id\":" << e.id << ",\"kind\":\"INTERCEPTION_CONTACT\""
		<< ",\"sourceUfoId\":" << e.contact.ufoId << ",\"sourceMissionId\":" << e.contact.missionId
		<< ",\"observedAt\":" << quote(e.contact.observedAt) << ",\"reportedAt\":" << quote(e.reportedAt)
		<< ",\"region\":" << quote(e.contact.region)
		<< ",\"longitude\":" << e.contact.longitude << ",\"latitude\":" << e.contact.latitude
		<< ",\"transmission\":\"SURVIVING_UFO_AT_ENCOUNTER_END\",\"observationConfidence\":100}";
	return out.str();
}
std::string beliefJson(const AlienRegionBelief &b)
{
	return "{\"kind\":\"INTERCEPTION_OBSERVED_IN_REGION\",\"region\":" + quote(b.region)
		+ ",\"confidence\":" + std::to_string(b.confidence)
		+ ",\"confidenceKind\":\"UNCALIBRATED_HEURISTIC\",\"independentSources\":"
		+ std::to_string(b.independentSources) + ",\"evidenceIds\":" + ids(b.evidenceIds) + "}";
}
std::string candidateJson(const AlienReconCandidate &c)
{
	return "{\"mission\":" + quote(c.mission) + ",\"region\":" + quote(c.region) + "}";
}
}

bool AlienReconCandidate::operator<(const AlienReconCandidate &other) const
{
	return std::tie(mission, region) < std::tie(other.mission, other.region);
}

int AlienCommand::monthlyAllowance(int month, int difficulty)
{
 static const int curves[5][18] = {
  {6,6,7,7,8,9,10,11,12,13,14,14,15,15,16,16,16,16},
  {7,7,8,9,10,11,13,15,17,18,19,20,21,22,22,23,23,23},
  {8,9,10,12,14,16,19,21,23,24,26,28,29,30,31,32,32,32},
  {9,10,11,13,15,18,21,24,27,29,31,33,35,36,37,38,38,38},
  {10,11,12,14,17,20,24,28,32,35,38,41,43,45,46,47,48,48}};
 if (month < 0 || difficulty < 0 || difficulty > 4) throw std::runtime_error("Invalid alien budget calendar/difficulty");
 return curves[difficulty][std::min(month,17)];
}
int AlienCommand::operationCost(const std::string &mission)
{
 if (mission == "STR_ALIEN_RESEARCH" || mission == "STR_ALIEN_PROBE_MISSION" || mission == "STR_ALIEN_RETALIATION") return 2;
 if (mission == "STR_ALIEN_HARVEST" || mission == "STR_ALIEN_ABDUCTION") return 3;
 if (mission == "STR_ALIEN_TERROR" || mission == "STR_ALIEN_SURFACE_ATTACK") return 4;
 if (mission == "STR_ALIEN_BASE" || mission == "STR_ALIEN_INFILTRATION") return 6;
 if (mission == "STR_ALIEN_SUPPLY") return 2;
 return -1; // Unpriced operations are never silently free.
}
void AlienCommand::beginBudgetMonth(int month, int difficulty)
{
 const int allowance = monthlyAllowance(month,difficulty);
 if (_budgetMonth == month) return;
 if (_budgetMonth > month) throw std::runtime_error("Alien budget cannot move backwards");
 // Start a new accounting epoch on first activation. No invented historical income/debt.
 const int carry = _budgetMonth < 0 ? 0 : std::min(_remaining, monthlyAllowance(_budgetMonth,_budgetDifficulty)/2);
 _remaining = allowance + carry + std::min(_pendingBonus, allowance/2);
 _pendingBonus = 0; _budgetMonth = month; _budgetDifficulty = difficulty;
}
bool AlienCommand::canFund(const std::string &mission) const
{
 const int cost = operationCost(mission);
 if (_budgetMonth < 0 || cost < 0 || cost > _remaining) return false;
 if (mission == "STR_ALIEN_BASE" || mission == "STR_ALIEN_SUPPLY") return _budgetMonth >= 1 && _logistics >= 2;
 if (mission == "STR_ALIEN_INFILTRATION") return _budgetMonth >= 2 && _adaptation >= 2 && _intelligence >= 1;
 return true;
}
bool AlienCommand::fundMission(int missionId, const std::string &mission)
{
 auto paid = _paidMissions.find(missionId);
 if (paid != _paidMissions.end()) return paid->second == mission;
 if (missionId <= 0 || !canFund(mission)) return false;
 _remaining -= operationCost(mission); _paidMissions.emplace(missionId,mission);
 if (mission == "STR_ALIEN_RETALIATION") _searchOnly.insert(missionId);
 return true;
}
std::string AlienCommand::budgetJson() const
{
 return "{\"policyVersion\":\"monthly-portfolio-v1\",\"epochMonth\":" + std::to_string(_budgetMonth)
 + ",\"difficulty\":" + std::to_string(_budgetDifficulty) + ",\"remaining\":" + std::to_string(_remaining)
 + ",\"pendingBonus\":" + std::to_string(_pendingBonus) + ",\"intelligence\":" + std::to_string(_intelligence)
 + ",\"logistics\":" + std::to_string(_logistics) + ",\"adaptation\":" + std::to_string(_adaptation)
 + ",\"allowance\":" + std::to_string(monthlyAllowance(_budgetMonth,_budgetDifficulty))
 + ",\"carryCap\":" + std::to_string(monthlyAllowance(_budgetMonth,_budgetDifficulty)/2)
 + ",\"nextAllowance\":" + std::to_string(monthlyAllowance(_budgetMonth+1,_budgetDifficulty))
 + ",\"nextBonusCap\":" + std::to_string(monthlyAllowance(_budgetMonth+1,_budgetDifficulty)/2)
 + ",\"maxOperations\":3,\"assaultAvailable\":false,\"terrorRewardVerified\":false}";
}
void AlienCommand::recordPortfolio(const std::string &time, const std::string &input, const std::string &response, const std::string &status)
{
 _portfolioMonth = _budgetMonth;
 _audit.push_back("{\"schemaVersion\":1,\"kind\":\"portfolio\",\"id\":" + std::to_string(_nextId++)
 + ",\"gameTime\":" + quote(time) + ",\"mode\":\"PORTFOLIO_EXECUTION\",\"status\":" + quote(status)
 + ",\"input\":" + input + ",\"response\":" + quote(response) + ",\"budgetAfter\":" + budgetJson() + "}");
}

void AlienCommand::updateBelief(const std::string &region)
{
	AlienRegionBelief belief;
	belief.region = region;
	std::set<int> sources;
	for (auto it = _evidence.rbegin(); it != _evidence.rend(); ++it)
	{
		if (it->contact.region == region && sources.insert(it->contact.ufoId).second
			&& belief.evidenceIds.size() < MAX_SUPPORT_PER_BELIEF)
			belief.evidenceIds.push_back(it->id);
	}
	belief.independentSources = (int)sources.size();
	// Confidence that interception has been observed, not that a base exists.
	belief.confidence = std::min(80, 30 + 10 * std::min(5, belief.independentSources));
	_beliefs[region] = belief;
}

bool AlienCommand::reportInterception(const AlienInterceptionContact &contact,
	const std::string &reportedAt, bool survived, const std::string &outcome)
{
	bool admitted = survived && validContact(contact) && !reportedAt.empty();
	std::string admission = !survived ? "REPORTER_LOST" : "INVALID_OR_UNOBSERVED_CONTACT";
	if (admitted)
	{
		for (const auto &e : _evidence)
		{
			if (e.contact.ufoId == contact.ufoId && e.contact.missionId == contact.missionId
				&& e.contact.observedAt == contact.observedAt && e.contact.region == contact.region)
			{
				admitted = false;
				admission = "DUPLICATE_CONTACT";
				break;
			}
		}
	}
	const int id = _nextId++;
	AlienInterceptionEvidence evidence;
	if (admitted)
	{
		evidence.id = id;
		evidence.contact = contact;
		evidence.reportedAt = reportedAt;
		_evidence.push_back(evidence);
		updateBelief(contact.region);
		admission = "ADMITTED";
	}
	// Rejected encounters stay audit-only; the policy never receives their locations.
	_audit.push_back("{\"schemaVersion\":1,\"kind\":\"interception\",\"id\":" + std::to_string(id)
		+ ",\"gameTime\":" + quote(reportedAt) + ",\"admission\":" + quote(admission)
		+ ",\"debugOutcome\":{\"sourceUfoId\":" + std::to_string(contact.ufoId)
		+ ",\"sourceMissionId\":" + std::to_string(contact.missionId) + ",\"status\":" + quote(outcome)
		+ "},\"evidence\":" + (admitted ? evidenceJson(evidence) : "null") + "}");
	return admitted;
}

AlienReconSnapshot AlienCommand::snapshot(std::vector<AlienReconCandidate> candidates) const
{
	AlienReconSnapshot result;
	std::sort(candidates.begin(), candidates.end());
	candidates.erase(std::unique(candidates.begin(), candidates.end(),
		[](const auto &a, const auto &b) { return !(a < b) && !(b < a); }), candidates.end());
	result.candidates = std::move(candidates);
	if (result.candidates.size() > MAX_CANDIDATES) return result;
	std::set<std::string> regions;
	std::set<int> support;
	for (const auto &c : result.candidates) regions.insert(c.region);
	for (const auto &pair : _beliefs)
	{
		if (regions.count(pair.first))
		{
			result.beliefs.push_back(pair.second);
			support.insert(pair.second.evidenceIds.begin(), pair.second.evidenceIds.end());
		}
	}
	for (const auto &e : _evidence)
		if (support.count(e.id)) result.evidence.push_back(e);
	return result;
}

AlienReconProposal AlienCommand::chooseRecon(const AlienReconSnapshot &input)
{
	AlienReconProposal proposal;
	proposal.reason = "NO_REPORTED_INTERCEPTIONS";
	if (input.candidates.empty()) { proposal.reason = "EMPTY_MENU"; return proposal; }
	if (input.candidates.size() > MAX_CANDIDATES) { proposal.reason = "MENU_LIMIT_EXCEEDED"; return proposal; }
	for (const auto &c : input.candidates)
		if (c.mission.empty() || c.region.empty()) { proposal.reason = "INVALID_MENU"; return proposal; }
	// Lexical ties are explicit and deterministic; never consume the campaign RNG.
	auto candidates = input.candidates;
	std::sort(candidates.begin(), candidates.end());
	for (const auto &c : candidates)
	{
		for (const auto &b : input.beliefs)
		{
			if (b.region != c.region || b.confidence < 1 || b.confidence > 100 || b.independentSources < 1 || b.evidenceIds.empty() || b.evidenceIds.size() > MAX_SUPPORT_PER_BELIEF) continue;
			const bool supported = std::all_of(b.evidenceIds.begin(), b.evidenceIds.end(), [&](int id) {
				return std::any_of(input.evidence.begin(), input.evidence.end(), [&](const auto &e) {
					return e.id == id && e.contact.region == b.region && validContact(e.contact);
				});
			});
			if (!supported) continue;
			const int score = b.confidence;
			if (score > proposal.score)
			{
				proposal.mission = c.mission;
				proposal.region = c.region;
				proposal.reason = "INVESTIGATE_REPORTED_INTERCEPTIONS";
				proposal.score = score;
				proposal.evidenceIds = b.evidenceIds;
			}
		}
	}
	return proposal;
}

bool AlienCommand::validateProposal(const AlienReconSnapshot &input, const AlienReconProposal &proposal)
{
	if (proposal.mission.empty() || proposal.region.empty() || proposal.reason.empty()
		|| proposal.score < 1 || proposal.score > 100 || input.candidates.size() > MAX_CANDIDATES
		|| proposal.evidenceIds.empty() || proposal.evidenceIds.size() > MAX_SUPPORT_PER_BELIEF) return false;
	if (!std::any_of(input.candidates.begin(), input.candidates.end(), [&](const auto &c) {
		return c.mission == proposal.mission && c.region == proposal.region;
	})) return false;
	std::set<int> uniqueIds;
	for (int id : proposal.evidenceIds)
	{
		if (!uniqueIds.insert(id).second || !std::any_of(input.evidence.begin(), input.evidence.end(), [&](const auto &e) {
			return e.id == id && e.contact.region == proposal.region && validContact(e.contact) && !e.reportedAt.empty();
		})) return false;
	}
	return std::any_of(input.beliefs.begin(), input.beliefs.end(), [&](const auto &b) {
		return b.region == proposal.region && b.confidence == proposal.score && b.independentSources > 0
			&& b.evidenceIds == proposal.evidenceIds;
	});
}

std::string AlienCommand::inputJson(const AlienReconSnapshot &input)
{
	return "{\"menuSource\":\"STATIC_RULESET_ONLY\",\"candidates\":" + array(input.candidates, candidateJson)
		+ ",\"beliefs\":" + array(input.beliefs, beliefJson) + ",\"evidence\":" + array(input.evidence, evidenceJson) + "}";
}

void AlienCommand::recordDecision(const std::string &gameTime, int difficulty, const std::string &script,
	const std::string &scope, const AlienReconSnapshot &input,
	const AlienReconProposal &proposal, const AlienCommandExecution &execution, const AlienCommandModelResult &model)
{
	const bool accepted = validateProposal(input, proposal);
	const std::string validation = scope != "RECON" ? "OUT_OF_SCOPE"
		: proposal.abstains() ? "ABSTAIN" : accepted ? "STATIC_MENU_VALID_SHADOW_ONLY" : "REJECTED";
	const std::string intent = model.proposal.abstains() ? "KEEP_ORIGINAL_SCHEDULE"
		: model.proposal.mission == "STR_ALIEN_RETALIATION" ? "SEARCH_FOR_XCOM_BASE" : "GATHER_INTERCEPTION_REPORTS";
	const bool modelExecuted = execution.source == "MODEL_COMMANDER" && execution.status == "MISSION_CREATED";
	const int id = _nextId++;
	_audit.push_back("{\"schemaVersion\":1,\"kind\":\"decision\",\"id\":" + std::to_string(id)
		+ ",\"gameTime\":" + quote(gameTime) + ",\"difficulty\":" + std::to_string(difficulty)
		+ ",\"script\":" + quote(script) + ",\"scope\":" + quote(scope)
		+ ",\"mode\":" + quote(modelExecuted ? "MODEL_EXECUTION" : "SHADOW") + ",\"policyVersion\":\"intent-operations-v2\""
		+ ",\"modelIntent\":" + quote(intent)
		+ ",\"expectedGain\":" + quote(intent == "SEARCH_FOR_XCOM_BASE" ? "BASE_DISCOVERY_CAN_TRIGGER_ASSAULT"
			: intent == "GATHER_INTERCEPTION_REPORTS" ? "SURVIVING_INTERCEPTION_REPORTS" : "ORIGINAL_CAMPAIGN_OBJECTIVES")
		+ ",\"input\":" + inputJson(input)
		+ ",\"proposal\":{\"mission\":" + quote(proposal.mission) + ",\"region\":" + quote(proposal.region)
		+ ",\"reason\":" + quote(proposal.reason) + ",\"score\":" + std::to_string(proposal.score)
		+ ",\"scoreKind\":\"UNCALIBRATED_HEURISTIC\",\"evidenceIds\":" + ids(proposal.evidenceIds) + "}"
		+ ",\"validation\":{\"status\":" + quote(validation) + ",\"executedProposal\":false}"
		+ ",\"model\":{\"status\":" + quote(model.status) + ",\"checkpointSha256\":" + quote(model.checkpointSha256)
		+ ",\"executedProposal\":" + (modelExecuted ? "true" : "false") + ",\"rawResponse\":" + quote(model.rawResponse)
		+ ",\"proposal\":{\"mission\":" + quote(model.proposal.mission) + ",\"region\":" + quote(model.proposal.region)
		+ ",\"reason\":" + quote(model.proposal.reason) + ",\"score\":" + std::to_string(model.proposal.score)
		+ ",\"evidenceIds\":" + ids(model.proposal.evidenceIds) + "}}"
		+ ",\"execution\":{\"source\":" + quote(execution.source) + ",\"status\":" + quote(execution.status)
		+ ",\"operationalStatus\":" + quote(execution.operationalStatus)
		+ ",\"missionId\":" + std::to_string(execution.missionId) + ",\"mission\":" + quote(execution.mission)
		+ ",\"region\":" + quote(execution.region) + ",\"race\":" + quote(execution.race)
		+ ",\"rngBefore\":" + quote(std::to_string(execution.rngBefore))
		+ ",\"rngAfter\":" + quote(std::to_string(execution.rngAfter)) + "}"
		+ ",\"outcome\":" + quote(execution.status == "MISSION_CREATED" ? "PENDING" : "NOT_CREATED") + "}");
}

void AlienCommand::recordBudgetFact(const std::string &event, int missionId, const std::string &mission, const std::string &time, int ufoId)
{
 if (missionId <= 0 || mission.empty()) return;
 if (_paidMissions.count(missionId) && _paidMissions.at(missionId) == mission && !_rewardedMissions.count(missionId))
 {
  if (event == "RESEARCH_FLIGHT_COMPLETED" && (mission == "STR_ALIEN_RESEARCH" || mission == "STR_ALIEN_PROBE_MISSION"))
  { _rewardedMissions.insert(missionId); ++_pendingBonus; ++_intelligence; }
  if (event == "PRODUCTIVE_ACTIVITY_COMPLETED" && (mission == "STR_ALIEN_HARVEST" || mission == "STR_ALIEN_ABDUCTION"))
  { _rewardedMissions.insert(missionId); _pendingBonus += 2; if (mission == "STR_ALIEN_HARVEST") ++_logistics; else ++_adaptation; }
 }
 const int id = _nextId++;
 _audit.push_back("{\"schemaVersion\":1,\"kind\":\"budget_fact\",\"id\":" + std::to_string(id)
  + ",\"gameTime\":" + quote(time) + ",\"event\":" + quote(event)
  + ",\"missionId\":" + std::to_string(missionId) + ",\"mission\":" + quote(mission)
  + ",\"sourceUfoId\":" + std::to_string(ufoId) + ",\"mode\":" + quote((_paidMissions.count(missionId)
   || event=="MISSION_DENIED_BUDGET_OR_PREREQUISITE" || event=="ASSAULT_DEFERRED_SEPARATE_COMMITMENT_REQUIRED")?"ENFORCED_ACCOUNTING":"SHADOW_ACCOUNTING") + "}");
}

void AlienCommand::recordBaseDiscovery(const AlienInterceptionContact &observer, double longitude, double latitude, const std::string &time)
{
 const int id = _nextId++;
 _audit.push_back("{\"schemaVersion\":1,\"kind\":\"base_discovery\",\"id\":" + std::to_string(id)
  + ",\"gameTime\":" + quote(time) + ",\"sourceUfoId\":" + std::to_string(observer.ufoId)
  + ",\"sourceMissionId\":" + std::to_string(observer.missionId)
  + ",\"longitude\":" + std::to_string(longitude) + ",\"latitude\":" + std::to_string(latitude)
  + ",\"mechanism\":\"ENGINE_BASE_SCAN\",\"knowledgeStatus\":\"ENGINE_RETALIATION_TARGET_FLAG\"}");
}

std::string AlienCommand::exportJsonl() const
{
	std::string result;
	for (const auto &event : _audit) result += event + "\n";
	return result;
}

void AlienCommand::save(YAML::YamlNodeWriter writer) const
{
	writer.setAsMap();
	writer.write("schemaVersion", 1);
	writer.write("nextId", _nextId);
	auto evidence = writer["evidence"];
	evidence.setAsSeq();
	for (const auto &e : _evidence)
	{
		auto w = evidence.write(); w.setAsMap();
		w.write("id", e.id); w.write("sourceUfoId", e.contact.ufoId); w.write("sourceMissionId", e.contact.missionId);
		w.write("observedAt", e.contact.observedAt); w.write("reportedAt", e.reportedAt); w.write("region", e.contact.region);
		w.write("longitude", e.contact.longitude); w.write("latitude", e.contact.latitude);
	}
	auto beliefs = writer["beliefs"]; beliefs.setAsSeq();
	for (const auto &pair : _beliefs)
	{
		const auto &b = pair.second;
		auto w = beliefs.write(); w.setAsMap();
		w.write("region", b.region); w.write("confidence", b.confidence);
		w.write("independentSources", b.independentSources); w.write("evidenceIds", b.evidenceIds);
	}
	writer.write("audit", _audit);
 if (budgetActive())
 {
  auto b = writer["budget"]; b.setAsMap(); b.write("version",1);
  b.write("month",_budgetMonth); b.write("difficulty",_budgetDifficulty); b.write("remaining",_remaining); b.write("bonus",_pendingBonus);
  b.write("portfolioMonth",_portfolioMonth);
  b.write("intelligence",_intelligence); b.write("logistics",_logistics); b.write("adaptation",_adaptation);
  auto paid = b["paid"]; paid.setAsSeq();
  for (const auto &p : _paidMissions) { auto w=paid.write(); w.setAsMap(); w.write("id",p.first); w.write("mission",p.second); }
  b.write("rewarded",std::vector<int>(_rewardedMissions.begin(),_rewardedMissions.end()));
  b.write("searchOnly",std::vector<int>(_searchOnly.begin(),_searchOnly.end()));
 }
}

void AlienCommand::load(const YAML::YamlNodeReader &reader)
{
	AlienCommand restored;
	if (!reader) { *this = std::move(restored); return; }
	if (reader["schemaVersion"].readVal<int>() != 1) throw YAML::Exception("Unsupported alien command schema");
	restored._nextId = reader["nextId"].readVal<int>();
	if (restored._nextId < 1) throw YAML::Exception("Invalid alien command event counter");
	std::set<int> evidenceIds;
	for (const auto &r : reader["evidence"].children())
	{
		AlienInterceptionEvidence e;
		e.id = r["id"].readVal<int>();
		e.contact.observed = true;
		e.contact.ufoId = r["sourceUfoId"].readVal<int>(); e.contact.missionId = r["sourceMissionId"].readVal<int>();
		e.contact.observedAt = r["observedAt"].readVal<std::string>();
		e.reportedAt = r["reportedAt"].readVal<std::string>(); e.contact.region = r["region"].readVal<std::string>();
		e.contact.longitude = r["longitude"].readVal<double>(); e.contact.latitude = r["latitude"].readVal<double>();
		if (!validContact(e.contact) || e.reportedAt.empty() || e.id <= 0 || e.id >= restored._nextId
			|| !evidenceIds.insert(e.id).second) throw YAML::Exception("Invalid alien command evidence");
		restored._evidence.push_back(e);
	}
	for (const auto &r : reader["beliefs"].children())
	{
		AlienRegionBelief b;
		b.region = r["region"].readVal<std::string>(); b.confidence = r["confidence"].readVal<int>();
		b.independentSources = r["independentSources"].readVal<int>(); r.readNode("evidenceIds", b.evidenceIds);
		if (b.region.empty() || b.confidence < 0 || b.confidence > 100 || b.independentSources < 1
			|| b.evidenceIds.empty() || b.evidenceIds.size() > MAX_SUPPORT_PER_BELIEF
			|| restored._beliefs.count(b.region)) throw YAML::Exception("Invalid alien command belief");
		for (int id : b.evidenceIds)
		{
			if (!std::any_of(restored._evidence.begin(), restored._evidence.end(), [&](const auto &e) {
				return e.id == id && e.contact.region == b.region;
			})) throw YAML::Exception("Alien belief references missing evidence");
		}
		restored._beliefs.emplace(b.region, b);
	}
	reader.tryRead("audit", restored._audit);
 if (reader["budget"])
 {
  auto b=reader["budget"];
  if (b["version"].readVal<int>() != 1) throw YAML::Exception("Unsupported alien budget");
  restored._budgetMonth=b["month"].readVal<int>(); restored._budgetDifficulty=b["difficulty"].readVal<int>();
  restored._portfolioMonth=b["portfolioMonth"].readVal<int>();
  if (restored._portfolioMonth < -1 || restored._portfolioMonth > restored._budgetMonth) throw YAML::Exception("Invalid portfolio calendar");
  restored._remaining=b["remaining"].readVal<int>(); restored._pendingBonus=b["bonus"].readVal<int>();
  restored._intelligence=b["intelligence"].readVal<int>(); restored._logistics=b["logistics"].readVal<int>(); restored._adaptation=b["adaptation"].readVal<int>();
  monthlyAllowance(restored._budgetMonth,restored._budgetDifficulty);
  if (restored._remaining < 0 || restored._pendingBonus < 0 || restored._intelligence < 0 || restored._logistics < 0 || restored._adaptation < 0) throw YAML::Exception("Invalid alien budget balance");
  for (const auto &p : b["paid"].children())
  {
   int id=p["id"].readVal<int>(); auto mission=p["mission"].readVal<std::string>();
   if (id<=0 || operationCost(mission)<0 || !restored._paidMissions.emplace(id,mission).second) throw YAML::Exception("Invalid alien budget commitment");
  }
  std::vector<int> ids; b.readNode("rewarded",ids);
  for (int id:ids) { if (!restored._paidMissions.count(id) || !restored._rewardedMissions.insert(id).second) throw YAML::Exception("Invalid alien budget reward"); }
  b.readNode("searchOnly",ids);
  for (int id:ids) { if (!restored._paidMissions.count(id) || restored._paidMissions.at(id)!="STR_ALIEN_RETALIATION" || !restored._searchOnly.insert(id).second) throw YAML::Exception("Invalid alien search commitment"); }
 }
	*this = std::move(restored);
}
}
