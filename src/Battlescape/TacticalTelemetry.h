// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "BattlescapeGame.h"
#include "AIModule.h"
#include "../Engine/Options.h"
#include "../Engine/RNG.h"
#include "../Engine/Logger.h"
#include "../Savegame/SavedBattleGame.h"
#include "../Savegame/BattleUnit.h"
#include "../Savegame/BattleItem.h"
#include "../Savegame/Node.h"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>

namespace OpenXcom
{
// An observer only: reads cached facts, never asks the AI to recalculate knowledge,
// never sets discovery/visibility, and never consumes campaign RNG.
class TacticalTelemetry
{
 std::ofstream _stream;
 unsigned long long _sequence = 0;
 bool _warned = false;
 static std::string quote(const std::string &s)
 {
  std::ostringstream out; out << '"';
  const char *hex = "0123456789abcdef";
  for (unsigned char c : s)
  {
   if (c == '"' || c == '\\') out << '\\' << c;
   else if (c < 32) out << "\\u00" << hex[c >> 4] << hex[c & 15];
   else out << c;
  }
  out << '"'; return out.str();
 }
 static std::string position(Position p)
 { return "[" + std::to_string(p.x) + "," + std::to_string(p.y) + "," + std::to_string(p.z) + "]"; }
 static const char *actionName(BattleActionType type)
 {
  switch (type)
  {
  case BA_NONE: return "NONE"; case BA_WALK: return "WALK";
  case BA_SNAPSHOT: return "SNAPSHOT"; case BA_AIMEDSHOT: return "AIMEDSHOT";
  case BA_AUTOSHOT: return "AUTOSHOT"; case BA_THROW: return "THROW";
  case BA_HIT: return "HIT"; case BA_PANIC: return "PANIC";
  case BA_MINDCONTROL: return "MINDCONTROL"; case BA_LAUNCH: return "LAUNCH";
  case BA_USE: return "USE"; case BA_RETHINK: return "RETHINK";
  case BA_TURN: return "TURN"; default: return "OTHER";
  }
 }
 void board(std::ostream &out, SavedBattleGame *battle)
 {
  out << ",\"mapSize\":[" << battle->getMapSizeX() << ',' << battle->getMapSizeY() << ',' << battle->getMapSizeZ()
      << "],\"nodes\":[";
  bool first = true;
  for (auto *node : *battle->getNodes()) if (!node->isDummy())
  {
   if (!first) out << ','; first = false;
   out << "{\"id\":" << node->getID() << ",\"position\":" << position(node->getPosition())
       << ",\"rank\":" << int(node->getRank()) << ",\"priority\":" << node->getFlags() << ",\"links\":[";
   for (size_t i = 0; i < node->getNodeLinks()->size(); ++i)
   { if (i) out << ','; out << node->getNodeLinks()->at(i); }
   out << "]}";
  }
  out << "],\"terrain\":["; first = true;
  for (int z = 0; z < battle->getMapSizeZ(); ++z)
   for (int y = 0; y < battle->getMapSizeY(); ++y)
    for (int x = 0; x < battle->getMapSizeX(); ++x)
    {
     auto *tile = battle->getTile(Position(x, y, z));
     int mask = (tile->getMapData(O_FLOOR) ? 1 : 0) | (tile->getMapData(O_WESTWALL) ? 2 : 0)
              | (tile->getMapData(O_NORTHWALL) ? 4 : 0) | (tile->getMapData(O_OBJECT) ? 8 : 0);
     if (!mask && !tile->getSmoke() && !tile->getFire()) continue;
     if (!first) out << ','; first = false;
     out << '[' << x << ',' << y << ',' << z << ',' << mask << ',' << tile->getSmoke() << ',' << tile->getFire() << ']';
    }
  out << ']';
 }
public:
 TacticalTelemetry()
 {
  // Each battle load gets its own capture; reopening/reloading never truncates one.
  auto ticks = std::chrono::system_clock::now().time_since_epoch().count();
  auto path = std::filesystem::u8path(Options::getMasterUserFolder() + "tactical-" + std::to_string(ticks) + ".jsonl");
  while (std::filesystem::exists(path))
   path = std::filesystem::u8path(Options::getMasterUserFolder() + "tactical-" + std::to_string(++ticks) + ".jsonl");
  _stream.open(path, std::ios::out | std::ios::binary);
  Log(LOG_INFO) << "Tactical telemetry: " << path.u8string();
 }
 void record(SavedBattleGame *battle, const char *event, const BattleAction *action = nullptr)
 {
  if (!_stream.good())
  {
   if (!_warned) { Log(LOG_WARNING) << "Tactical telemetry unavailable; capture stopped. Gameplay continues."; _warned = true; }
   return;
  }
  std::ostringstream out;
  out << "{\"protocol\":\"tactical-telemetry-v1\",\"sequence\":" << ++_sequence
      << ",\"event\":" << quote(event) << ",\"turn\":" << battle->getTurn() << ",\"side\":" << int(battle->getSide())
      << ",\"mission\":" << quote(battle->getMissionType()) << ",\"rng\":" << quote(std::to_string(RNG::getSeed()))
      << ",\"observer\":" << (Options::tacticalObserver ? "true" : "false")
      << ",\"defendExperiment\":" << (Options::tacticalDefend ? "true" : "false")
      << ",\"debugMode\":" << (battle->getDebugMode() ? "true" : "false")
      << ",\"nativeCheating\":" << (battle->isCheating() ? "true" : "false");
  if (action)
  {
   const auto *ai=action->actor ? action->actor->getAIModule() : nullptr;
   const bool ordered=Options::tacticalDefend && ai && (ai->getDefendStatus()=="MOVING" || ai->getDefendStatus()=="HOLDING");
   out << ",\"action\":{\"actor\":" << (action->actor ? action->actor->getId() : -1)
       << ",\"controller\":" << quote(std::string(event)=="AI_DECISION" ? (ordered ? "DEFEND_AREA" : "NATIVE") : "STATE_EXECUTION")
       << ",\"type\":" << quote(actionName(action->type)) << ",\"typeCode\":" << int(action->type)
       << ",\"target\":" << position(action->target) << ",\"result\":" << quote(action->result)
       // A resolved state may already have consumed/deleted its item. Only
       // dereference a weapon while the fresh AI proposal still owns it.
       << ",\"weapon\":" << quote(std::string(event) == "AI_DECISION" && action->weapon ? action->weapon->getRules()->getType() : "")
       << ",\"finalFacing\":" << action->finalFacing << ",\"finalAction\":" << (action->finalAction ? "true" : "false") << '}';
  }
  out << ",\"units\":["; bool first = true;
  for (auto *unit : *battle->getUnits())
  {
   if (!first) out << ','; first = false;
   const auto *ai = unit->getAIModule();
   out << "{\"id\":" << unit->getId() << ",\"type\":" << quote(unit->getType())
       << ",\"faction\":" << int(unit->getFaction()) << ",\"originalFaction\":" << int(unit->getOriginalFaction())
       << ",\"position\":" << position(unit->getPosition()) << ",\"direction\":" << unit->getDirection()
       << ",\"status\":" << int(unit->getStatus()) << ",\"out\":" << (unit->isOut() ? "true" : "false")
       << ",\"health\":" << unit->getHealth() << ",\"stun\":" << unit->getStunlevel() << ",\"morale\":" << unit->getMorale()
       << ",\"tu\":" << unit->getTimeUnits() << ",\"energy\":" << unit->getEnergy()
       << ",\"playerVisible\":" << (unit->getVisible() ? "true" : "false")
       << ",\"aiMode\":" << (ai ? ai->getModeForTelemetry() : -1)
       << ",\"fromNode\":" << (ai && ai->getFromNodeForTelemetry() ? ai->getFromNodeForTelemetry()->getID() : -1)
       << ",\"toNode\":" << (ai && ai->getToNodeForTelemetry() ? ai->getToNodeForTelemetry()->getID() : -1)
       << ",\"order\":{\"policy\":\"defend-area-v1\",\"revision\":" << (ai ? ai->getDefendRevision() : 0)
       << ",\"id\":" << quote(ai && ai->getDefendRevision()>0 ? std::to_string(unit->getId())+":"+std::to_string(ai->getDefendRevision()) : "")
       << ",\"assignedTurn\":" << (ai ? ai->getDefendAssignedTurn() : -1)
       << ",\"post\":" << position(ai ? ai->getDefendPost() : Position(-1,-1,-1))
       << ",\"role\":" << quote(ai ? ai->getDefendRole() : "")
       << ",\"status\":" << quote(ai ? ai->getDefendStatus() : "") << '}'
       << ",\"visibleIds\":[";
   bool firstContact = true;
   for (auto *contact : *unit->getVisibleUnits())
   { if (!firstContact) out << ','; firstContact = false; out << contact->getId(); }
   out << "]}";
  }
  out << ']';
  const std::string kind(event);
  if (kind == "BATTLE_OPEN" || kind == "SIDE_START" || kind == "SIDE_READY") board(out, battle);
  out << "}\n";
  _stream << out.str(); _stream.flush();
  if (!_stream.good() && !_warned)
  { Log(LOG_WARNING) << "Tactical telemetry write failed; capture is incomplete."; _warned = true; }
 }
};
}
