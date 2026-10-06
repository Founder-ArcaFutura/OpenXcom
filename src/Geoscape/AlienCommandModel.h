// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "../Savegame/AlienCommand.h"
namespace OpenXcom
{
// Value-only admitted input, fixed loopback endpoint, shadow-only output.
AlienCommandModelResult queryAlienReconModel(const AlienReconSnapshot &input, int port);
AlienCommandModelResult validateAlienReconModelResponse(const AlienReconSnapshot &input, const std::string &response);
std::string queryAlienPortfolioModel(const std::string &body, int port);
}
