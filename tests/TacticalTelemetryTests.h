// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "../src/Battlescape/BattlescapeState.h"
#include "../src/Battlescape/Map.h"
#include "../src/Battlescape/TacticalTelemetry.h"
#include "../src/Battlescape/BattleState.h"
#include <typeinfo>

std::string persistentOrderSnapshot(SavedBattleGame *battle)
{
 std::ostringstream out; out << '{'; bool first=true;
 // Match native load eligibility: dead/ignored/player-controlled units do not
 // restore AI modules. Their historical orders remain in telemetry.
 for (auto *u : *battle->getUnits()) if (u->getFaction()!=FACTION_PLAYER && u->getStatus()!=STATUS_DEAD &&
     !u->isIgnored() && u->getAIModule() && u->getAIModule()->getDefendRevision()>0)
 {
  auto *a=u->getAIModule(); if (!first) out << ','; first=false;
  out << TacticalProbe::quote(std::to_string(u->getId())) << ":{\"revision\":" << a->getDefendRevision()
      << ",\"post\":" << TacticalProbe::position(a->getDefendPost()) << ",\"assignedTurn\":" << a->getDefendAssignedTurn()
      << ",\"status\":" << TacticalProbe::quote(a->getDefendStatus()) << ",\"role\":" << TacticalProbe::quote(a->getDefendRole()) << '}';
 }
 out << '}'; return out.str();
}

void verifyTacticalCheckpoint(Game &game)
{
 auto *save=new SavedGame(); game.setSavedGame(save); save->load("source.sav",game.getMod(),game.getLanguage());
 check(save->getSavedBattle()!=nullptr,"Checkpoint lost battle");
 check(CrossPlatform::writeFile(Options::getMasterUserFolder()+"loaded-orders.json",persistentOrderSnapshot(save->getSavedBattle())),"Cannot export reloaded orders");
 std::cout << "PASS: native checkpoint loaded in fresh process" << std::endl;
}

// Runs the real state machine on a disposable battle. XCOM holds its turn;
// native aliens/civilians act. Presentation overlays are dismissed by the test.
void tacticalTurnReplay(Game &game)
{
 auto *save = new SavedGame(); game.setSavedGame(save);
 save->load("source.sav", game.getMod(), game.getLanguage());
 auto *battle = save->getSavedBattle();
 check(battle && !battle->getDebugMode(), "Turn replay requires a non-debug battlescape save");
 battle->loadMapResources(game.getMod());
 const int initialTurn = battle->getTurn();
 const char *phaseArg = std::getenv("OPENXCOM_TACTICAL_PHASES");
 const int phases = phaseArg ? std::stoi(phaseArg) : 1;
 check(phases>=1 && phases<=6, "Replay supports one to six alien phases");
 check(battle->getSide() == FACTION_PLAYER, "Turn replay starts on a player-side snapshot");
 auto *floor = new State(); game.pushState(floor);
 auto *state = new BattlescapeState(); battle->setBattleState(state);
 game.pushState(state); state->init();
 const auto before = TacticalProbe::snapshot(battle); const auto seed = RNG::getSeed();
 state->getMap()->invalidate(); state->getMap()->draw();
 state->blit(); game.getScreen()->flip();
 game.getScreen()->screenshot(Options::getMasterUserFolder() + "inspection.png");
 check(TacticalProbe::snapshot(battle) == before && RNG::getSeed() == seed,
       "Observer rendering changed battle state or campaign RNG");
 auto *engine = state->getBattleGame();
 engine->recordTelemetry("TEST_RENDER_CHECK");
 check(TacticalProbe::snapshot(battle) == before && RNG::getSeed() == seed,
       "Telemetry changed battle state or campaign RNG");
 engine->requestEndTurn(false);
 bool sawAlien = battle->getSide() == FACTION_HOSTILE;
 int steps = 0;
 for (; steps < 5000; ++steps)
 {
  // NextTurn and informational overlays normally await a click. The harness
  // dismisses them; it does not bypass native battle/action state execution.
  for (int overlay = 0; !game.isState(state) && overlay < 32; ++overlay)
  {
   check(!game.isState(floor), "Battle finished before the requested phase; capture is retained");
   game.popState();
  }
  check(game.isState(state), "Battle ended or an unsupported overlay interrupted turn replay");
  if (sawAlien && battle->getSide() == FACTION_PLAYER && battle->getTurn() > initialTurn && !engine->isBusy())
  {
   engine->recordTelemetry("TEST_PHASE_COMPLETE");
   const auto suffix=std::to_string(battle->getTurn());
   save->save("checkpoint-"+suffix+".sav", game.getMod());
   check(CrossPlatform::writeFile(Options::getMasterUserFolder()+"orders-"+suffix+".json",persistentOrderSnapshot(battle)),"Cannot export checkpoint orders");
   if (battle->getTurn() >= initialTurn+phases) break;
   sawAlien=false; state->init(); engine->think(); engine->requestEndTurn(false);
  }
  engine->think();
  check(save->getSavedBattle() == battle, "Battle was removed during the requested phase");
  engine->handleState();
  check(save->getSavedBattle() == battle, "Battle was removed while resolving an action");
  engine->cleanupDeleted();
  // Explosion states wait for the map's flash frame to be rendered. Advance
  // presentation as well as the simulation, without adding wall-clock sleeps.
  state->animate(); state->getMap()->draw(); state->blit();
  if (battle->getSide() == FACTION_HOSTILE) sawAlien = true;
 }
 if (steps >= 5000)
 {
  std::cerr << "REPLAY_BOUND: turn=" << battle->getTurn() << " side=" << int(battle->getSide())
            << " states=" << engine->getStates().size() << " alienSeen=" << sawAlien << std::endl;
  for (auto *pending : engine->getStates()) if (pending) std::cerr << "PENDING: " << typeid(*pending).name() << std::endl;
 }
 check(steps < 5000 && sawAlien && battle->getTurn() > initialTurn, "Alien turn replay did not complete within bound");
 engine->recordTelemetry("TEST_COMPLETE");
 const auto finalSeed = RNG::getSeed();
 check(CrossPlatform::writeFile(Options::getMasterUserFolder() + "final-battle.yaml", TacticalProbe::snapshot(battle)), "Cannot export turn result");
 check(CrossPlatform::writeFile(Options::getMasterUserFolder() + "final-rng.txt", std::to_string(finalSeed)), "Cannot export RNG result");
 std::cout << "PASS: native alien phase completed after " << steps << " ticks; turn " << initialTurn << " -> " << battle->getTurn() << std::endl;
}
