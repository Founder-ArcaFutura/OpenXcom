// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once
#include "../Savegame/AlienCommand.h"

namespace OpenXcom
{
class Mod;
class RuleMissionScript;
class Ufo;
class GameTime;
class Game;
class Globe;
std::vector<AlienReconCandidate> buildAlienPortfolioMenu(const Mod &mod, const class SavedGame &save);
void executeAlienPortfolio(Game &game, const Globe &globe);

/// Rules-only catalog. It deliberately does not accept a SavedGame.
std::vector<AlienReconCandidate> buildAlienReconMenu(const Mod &mod);
AlienInterceptionContact captureAlienInterceptionContact(const Mod &mod, const Ufo &ufo, const GameTime &time);

/// Validate a model proposal; the engine may explicitly opt into execution.
class AlienCommandMissionAudit
{
	AlienCommand *_command;
	std::string _time, _script, _scope;
	int _difficulty, _exceptions;
	AlienReconSnapshot _input;
	AlienReconProposal _proposal;
	AlienCommandExecution _execution;
	AlienCommandModelResult _model;
public:
	AlienCommandMissionAudit(AlienCommand *command, const Mod &mod,
		const RuleMissionScript &script, const std::string &time, int difficulty);
	~AlienCommandMissionAudit() noexcept;
	bool executableProposal(AlienReconProposal &proposal) const;
	void operationalStatus(const std::string &status);
	void executed(int id, const std::string &mission, const std::string &region, const std::string &race);
};
}
