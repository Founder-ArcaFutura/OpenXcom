// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once
#include <cstddef>
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace OpenXcom
{
namespace YAML { class YamlNodeReader; class YamlNodeWriter; }

// Observation DTO: only the reporting UFO's contact location and own identifiers.
struct AlienInterceptionContact
{
	bool observed = false;
	int ufoId = 0, missionId = 0;
	std::string observedAt, region;
	double longitude = 0, latitude = 0;
};

struct AlienInterceptionEvidence
{
	int id = 0;
	AlienInterceptionContact contact;
	std::string reportedAt;
};

struct AlienRegionBelief
{
	std::string region;
	int confidence = 0, independentSources = 0;
	std::vector<int> evidenceIds;
};

struct AlienReconCandidate
{
	std::string mission, region;
	bool operator<(const AlienReconCandidate &other) const;
};

// This is the entire policy interface. No game, mod, base, craft or save pointers.
struct AlienReconSnapshot
{
	std::vector<AlienReconCandidate> candidates;
	std::vector<AlienRegionBelief> beliefs;
	std::vector<AlienInterceptionEvidence> evidence;
};

struct AlienReconProposal
{
	std::string mission, region, reason;
	int score = 0;
	std::vector<int> evidenceIds;
	bool abstains() const { return mission.empty() && region.empty(); }
};

struct AlienCommandModelResult
{
	std::string status = "DISABLED", checkpointSha256, rawResponse;
	AlienReconProposal proposal;
};

struct AlienCommandExecution
{
	std::string source = "LEGACY_COMMANDER", status = "NO_MISSION_CREATED", mission, region, race;
	std::string operationalStatus = "NOT_REQUESTED";
	int missionId = 0;
	uint64_t rngBefore = 0, rngAfter = 0;
};

/**
 * Persistent alien knowledge and decision receipts. All inference uses explicit
 * observation DTOs. Loading restores beliefs; it never rebuilds them from game state.
 */
class AlienCommand
{
 int _budgetMonth = -1, _budgetDifficulty = 0, _remaining = 0, _pendingBonus = 0;
 int _intelligence = 0, _logistics = 0, _adaptation = 0;
 std::map<int, std::string> _paidMissions;
 std::set<int> _rewardedMissions, _searchOnly;
 int _portfolioMonth = -1;
	int _nextId = 1;
	std::vector<AlienInterceptionEvidence> _evidence;
	std::map<std::string, AlienRegionBelief> _beliefs;
	std::vector<std::string> _audit;
	void updateBelief(const std::string &region);
public:
 static int monthlyAllowance(int month, int difficulty);
 static int operationCost(const std::string &mission);
 void beginBudgetMonth(int month, int difficulty);
 bool budgetActive() const { return _budgetMonth >= 0; }
 int remainingBudget() const { return _remaining; }
 int budgetMonth() const { return _budgetMonth; }
 bool portfolioDue() const { return _portfolioMonth != _budgetMonth; }
 bool canFund(const std::string &mission) const;
 bool fundMission(int missionId, const std::string &mission);
 bool searchOnly(int missionId) const { return _searchOnly.count(missionId) != 0; }
 std::string budgetJson() const;
 void recordPortfolio(const std::string &time, const std::string &input, const std::string &response, const std::string &status);
	void recordBudgetFact(const std::string &event, int missionId, const std::string &mission, const std::string &time, int ufoId = 0);
	void recordBaseDiscovery(const AlienInterceptionContact &observer, double longitude, double latitude, const std::string &time);
	static constexpr size_t MAX_CANDIDATES = 64;
	static constexpr size_t MAX_SUPPORT_PER_BELIEF = 8;
	bool empty() const { return _audit.empty() && _evidence.empty() && _beliefs.empty(); }
	void load(const YAML::YamlNodeReader &reader);
	void save(YAML::YamlNodeWriter writer) const;
	// Admission is conservative: an observed encounter and a surviving reporting UFO.
	bool reportInterception(const AlienInterceptionContact &contact,
		const std::string &reportedAt, bool survived, const std::string &outcome);
	AlienReconSnapshot snapshot(std::vector<AlienReconCandidate> candidates) const;
	static AlienReconProposal chooseRecon(const AlienReconSnapshot &input);
	static std::string inputJson(const AlienReconSnapshot &input);
	static bool validateProposal(const AlienReconSnapshot &input, const AlienReconProposal &proposal);
	void recordDecision(const std::string &gameTime, int difficulty, const std::string &script,
		const std::string &scope, const AlienReconSnapshot &input,
		const AlienReconProposal &proposal, const AlienCommandExecution &execution, const AlienCommandModelResult &model = {});
	std::string exportJsonl() const;
	const std::vector<std::string> &getAudit() const { return _audit; }
	const std::vector<AlienInterceptionEvidence> &getEvidence() const { return _evidence; }
	const std::map<std::string, AlienRegionBelief> &getBeliefs() const { return _beliefs; }
};
}
