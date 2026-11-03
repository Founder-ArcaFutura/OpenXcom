// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only destination experiment. Does not invoke think(), move units, or advance turns.
#pragma once
#include "../src/Savegame/SavedBattleGame.h"
#include "../src/Savegame/BattleUnit.h"
#include "../src/Savegame/Node.h"
#include "../src/Battlescape/AIModule.h"
#include "../src/Battlescape/Pathfinding.h"
#include <set>

namespace TacticalProbe
{
std::string quote(const std::string &s)
{
 std::ostringstream out; out << '"';
 for (unsigned char c : s)
 {
  if (c == '"' || c == '\\') out << '\\' << c;
  else if (c < 32) { const char *hex = "0123456789abcdef"; out << "\\u00" << hex[c >> 4] << hex[c & 15]; }
  else out << c;
 }
 out << '"'; return out.str();
}
std::string position(Position p)
{ return "[" + std::to_string(p.x) + "," + std::to_string(p.y) + "," + std::to_string(p.z) + "]"; }
std::string snapshot(SavedBattleGame *battle)
{ YAML::YamlRootNodeWriter w; battle->save(w.toBase()); return w.emit().yaml; }
int objectiveDistance(Position p, const std::vector<Node*> &objective)
{
 int distance = std::numeric_limits<int>::max();
 for (auto *node : objective) distance = std::min(distance, Position::distanceSq(p, node->getPosition()));
 return distance;
}
struct Path { bool reachable = false; int tu = -1; int energy = 0; std::vector<int> steps; };
Path pathTo(SavedBattleGame *battle, BattleUnit *unit, Position target)
{
 Path result;
 if (unit->getPosition() == target) { result.reachable = true; result.tu = 0; return result; }
 auto *pf = battle->getPathfinding();
 pf->calculate(unit, target, BAM_NORMAL);
 result.reachable = pf->getStartDirection() != -1;
 if (result.reachable)
 {
  result.tu = pf->getTotalTUCost(); result.steps = pf->copyPath();
  Position endpoint = unit->getPosition();
  for (auto step = result.steps.rbegin(); step != result.steps.rend(); ++step)
  {
   const auto move = pf->getTUCost(endpoint, *step, unit, nullptr, BAM_NORMAL);
   endpoint = move.pos; result.energy += move.cost.energy;
  }
  // Pathfinding may adjust a destination's height. Only accept the exact post.
  if (endpoint != target) { result.reachable = false; result.tu = -1; result.steps.clear(); }
 }
 pf->abortPath(); return result;
}
// Restore node reservations between arms, including reservations owned by inactive aliens.
struct Reservations
{
 std::vector<std::pair<Node*, bool>> original;
 explicit Reservations(SavedBattleGame *battle)
 { for (auto *n : *battle->getNodes()) original.emplace_back(n, n->isAllocated()); }
 void restore() const
 { for (auto pair : original) { if (pair.second) pair.first->allocateNode(); else pair.first->freeNode(); } }
 ~Reservations() { restore(); }
};
Node *fromNode(SavedBattleGame *battle, BattleUnit *unit)
{
 Node *nearest = nullptr; int distance = std::numeric_limits<int>::max();
 for (auto *n : *battle->getNodes())
 {
  if (n->isDummy() || n->getPosition().z != unit->getPosition().z ||
      ((n->getType() & Node::TYPE_SMALL) && !unit->isSmallUnit())) continue;
  int d = Position::distanceSq(unit->getPosition(), n->getPosition());
  if (d < distance) { nearest = n; distance = d; }
 }
 return nearest;
}
// Node::save intentionally omits segment. Legacy saves retain a separate [x][y]
// map-block identity grid. This identifies the footprint, not original node provenance.
int footprint(SavedBattleGame *battle, Mod *mod, Node *node)
{
 auto p = node->getPosition();
 auto &grid = battle->getFlattenedMapTerrainNames();
 if (p.x < 0 || p.y < 0 || size_t(p.x / 10) >= grid.size() ||
     size_t(p.y / 10) >= grid[p.x / 10].size()) return 0;
 const auto &name = grid[p.x / 10][p.y / 10];
 if (mod->getUfo(name, false)) return Node::UFOSEGMENT;
 if (mod->getCraft(name, false)) return Node::CRAFTSEGMENT;
 return 0;
}
std::string order(BattleUnit *unit, Node *target, const std::string &role, const Path &path,
                  const std::vector<Node*> &objective)
{
 const Position end = target ? target->getPosition() : unit->getPosition();
 std::ostringstream out;
 out << "{\"unit\":" << unit->getId() << ",\"type\":" << quote(unit->getType())
     << ",\"role\":" << quote(role) << ",\"start\":" << position(unit->getPosition())
     << ",\"target\":" << position(end) << ",\"node\":" << (target ? target->getID() : -1)
     << ",\"currentTU\":" << unit->getTimeUnits() << ",\"currentEnergy\":" << unit->getEnergy()
     << ",\"movementEnergy\":" << path.energy << ",\"pathExists\":" << (path.reachable ? "true" : "false")
     << ",\"movementTU\":" << path.tu << ",\"fitsCurrentTU\":"
     << (path.reachable && path.tu <= unit->getTimeUnits() ? "true" : "false")
     << ",\"startObjectiveDistanceSq\":" << objectiveDistance(unit->getPosition(), objective)
     << ",\"targetObjectiveDistanceSq\":" << objectiveDistance(end, objective) << ",\"pathDirectionsReverse\":[";
 for (size_t i = 0; i < path.steps.size(); ++i) { if (i) out << ','; out << path.steps[i]; }
 out << "]}"; return out.str();
}
}

void battlescapeProbe(Game &game)
{
 using namespace TacticalProbe;
 auto *save = new SavedGame(); game.setSavedGame(save);
 save->load("source.sav", game.getMod(), game.getLanguage());
 auto *battle = save->getSavedBattle();
 check(battle != nullptr, "Probe requires an in-battle save, not a Geoscape save");
 battle->loadMapResources(game.getMod());
 const auto seed = RNG::getSeed();
 const auto before = snapshot(battle);
 Reservations reservations(battle);
 std::vector<Node*> objective;
 for (auto *n : *battle->getNodes())
  if (!n->isDummy() && n->getRank() >= NR_SOLDIER && footprint(battle, game.getMod(), n) == Node::UFOSEGMENT) objective.push_back(n);
 check(!objective.empty(), "UFO defence probe requires guard-ranked nodes in saved UFO footprint");
 std::vector<BattleUnit*> units;
 for (auto *u : *battle->getUnits())
  if (!u->isOut() && u->getFaction() == FACTION_HOSTILE && u->getOriginalFaction() == FACTION_HOSTILE)
   units.push_back(u);
 check(!units.empty(), "No active original hostile units in this save");
 std::sort(units.begin(), units.end(), [](BattleUnit *a, BattleUnit *b) { return a->getId() < b->getId(); });
 const char *seedArg = std::getenv("OPENXCOM_BATTLESCAPE_SEED");
 const uint64_t probeSeed = seedArg ? std::stoull(seedArg) : 1;
 check(probeSeed != 0, "Probe seed must be nonzero");
 RNG::setSeed(probeSeed);
 std::ostringstream baseline;
 for (size_t i = 0; i < units.size(); ++i)
 {
  auto *u = units[i]; Node *from = fromNode(battle, u); Node *target = nullptr;
  if (u->getAIModule())
  {
   YAML::YamlRootNodeWriter w; u->getAIModule()->save(w.toBase());
   YAML::YamlRootNodeReader r(YAML::YamlString(w.emit().yaml), "saved patrol state");
   int fromId = r["fromNode"].readVal(-1), toId = r["toNode"].readVal(-1);
   if (fromId >= 0 && size_t(fromId) < battle->getNodes()->size()) from = battle->getNodes()->at(fromId);
   if (toId >= 0 && size_t(toId) < battle->getNodes()->size()) target = battle->getNodes()->at(toId);
  }
  if (target && target->getPosition() == u->getPosition()) { from = target; target->freeNode(); target = nullptr; }
  const bool scout = battle->isCheating() || !from || from->getRank() == NR_SCOUT ||
     (battle->getTile(u->getPosition()) && battle->getTile(u->getPosition())->getFire());
  Path path;
  if (target) path = pathTo(battle, u, target->getPosition());
  else for (int attempt = 0; attempt < 5 && !target; ++attempt)
  {
   target = battle->getPatrolNode(scout, u, from);
   if (!target) target = battle->getPatrolNode(!scout, u, from);
   if (target) { path = pathTo(battle, u, target->getPosition()); if (!path.reachable) target = nullptr; }
  }
  if (target) target->allocateNode();
  if (i) baseline << ',';
  baseline << order(u, target, scout ? "SCOUT_PATROL_PROBE" : "GUARD_PATROL_PROBE", path, objective);
 }
 reservations.restore(); RNG::setSeed(seed);
 // A new shared order replaces these active units' old destination reservations.
 for (auto *u : units) if (u->getAIModule())
 {
  YAML::YamlRootNodeWriter w; u->getAIModule()->save(w.toBase());
  YAML::YamlRootNodeReader r(YAML::YamlString(w.emit().yaml), "release old destination");
  int id = r["toNode"].readVal(-1);
  if (id >= 0 && size_t(id) < battle->getNodes()->size()) battle->getNodes()->at(id)->freeNode();
 }
 std::stable_sort(units.begin(), units.end(), [&](BattleUnit *a, BattleUnit *b)
 { return objectiveDistance(a->getPosition(), objective) < objectiveDistance(b->getPosition(), objective); });
 std::ostringstream coordinated; std::vector<Position> assigned;
 const size_t guards = (2 * units.size() + 2) / 3;
 for (size_t i = 0; i < units.size(); ++i)
 {
  auto *u = units[i]; const bool guard = i < guards;
  Node *best = nullptr; Path bestPath; int bestScore = std::numeric_limits<int>::max();
  for (auto *n : *battle->getNodes())
  {
   auto *tile = battle->getTile(n->getPosition());
   if (n->isDummy() || n->isAllocated() || !tile || tile->getFire() || tile->getDangerous() ||
       (n->getType() & Node::TYPE_DANGEROUS) || footprint(battle, game.getMod(), n) == Node::CRAFTSEGMENT ||
       ((n->getType() & Node::TYPE_SMALL) && !u->isSmallUnit()) ||
       ((n->getType() & Node::TYPE_FLYING) && u->getMovementType() != MT_FLY) ||
       !battle->setUnitPosition(u, n->getPosition(), true)) continue;
   const int d = objectiveDistance(n->getPosition(), objective);
   const bool interior = std::find(objective.begin(), objective.end(), n) != objective.end();
   if ((guard && !interior) ||
       (!guard && (footprint(battle, game.getMod(), n) == Node::UFOSEGMENT || d > 64))) continue;
   bool crowded = false;
   for (Position p : assigned) if (Position::distanceSq(p, n->getPosition()) < 9) crowded = true;
   if (crowded) continue;
   Path path = pathTo(battle, u, n->getPosition());
   if (!path.reachable || path.tu > std::max(0, u->getTimeUnits() - 12) || path.energy > u->getEnergy()) continue;
   // Prefer inexpensive guard posts; screens aim about four tiles outside UFO nodes.
   const int score = path.tu + (guard ? 0 : std::abs(d - 16));
   if (score < bestScore) { best = n; bestPath = path; bestScore = score; }
  }
  if (best)
  {
   check(bestPath.reachable && bestPath.tu <= std::max(0, u->getTimeUnits() - 12) && bestPath.energy <= u->getEnergy(), "Order exceeds movement budget");
   best->allocateNode(); assigned.push_back(best->getPosition());
  }
  else { bestPath = pathTo(battle, u, u->getPosition()); assigned.push_back(u->getPosition()); }
  if (i) coordinated << ',';
  coordinated << order(u, best, best ? (guard ? "UFO_GUARD" : "OUTER_SCREEN") : "HOLD_NO_VALID_POST", bestPath, objective);
 }
 reservations.restore();
 check(RNG::getSeed() == seed, "Coordinated assignment consumed campaign RNG");
 check(snapshot(battle) == before, "Destination probe changed serialized battle state");
 std::ostringstream out;
 out << "{\"protocol\":\"battlescape-destinations-v1\",\"scope\":\"DESTINATION_FEASIBILITY_ONLY\","
     << "\"objectiveSource\":\"SAVED_UFO_MAP_FOOTPRINT_AND_GUARD_NODE_RANK\","
     << "\"mission\":" << quote(battle->getMissionType()) << ",\"turn\":" << battle->getTurn()
     << ",\"side\":" << int(battle->getSide()) << ",\"seed\":" << probeSeed
     << ",\"movementReserveTU\":12,\"battleStateUnchanged\":true,\"rngUnchanged\":true,\"mapSize\":["
     << battle->getMapSizeX() << ',' << battle->getMapSizeY() << ',' << battle->getMapSizeZ()
     << "],\"nodes\":[";
 bool first = true;
 for (auto *n : *battle->getNodes()) if (!n->isDummy())
 {
  if (!first) out << ','; first = false;
  out << "{\"id\":" << n->getID() << ",\"position\":" << position(n->getPosition())
      << ",\"originalSegment\":" << n->getSegment() << ",\"footprint\":" << footprint(battle, game.getMod(), n)
      << ",\"objectiveAnchor\":" << (std::find(objective.begin(), objective.end(), n) != objective.end() ? "true" : "false")
      << ",\"rank\":" << int(n->getRank()) << '}';
 }
 out << "],\"baseline\":[" << baseline.str() << "],\"coordinated\":[" << coordinated.str() << "]}";
 check(CrossPlatform::writeFile(Options::getMasterUserFolder() + "tactical-probe.json", out.str()), "Cannot write tactical probe");
 std::cout << "PASS: " << checks << " tactical checks; " << units.size() << " active aliens; " << assigned.size()
           << " orders; original battle state and RNG preserved" << std::endl;
}
