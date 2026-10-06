// SPDX-License-Identifier: GPL-3.0-or-later
#include "AlienCommandModel.h"
#include "../Engine/Yaml.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#include <winhttp.h>
#ifdef _MSC_VER
#pragma comment(lib, "winhttp.lib")
#endif
#endif

namespace OpenXcom
{
std::string queryAlienPortfolioTransport(const std::string &body, int port, const wchar_t *endpoint);
AlienCommandModelResult validateAlienReconModelResponse(const AlienReconSnapshot &input, const std::string &response)
{
	AlienCommandModelResult result;
	result.status = "REJECTED_MODEL_RESPONSE";
	if (response.size() > 65536) return result;
	try
	{
		YAML::YamlRootNodeReader r(YAML::YamlString(response), "alien model response");
		if (r["schemaVersion"].readVal<int>() != 1) return result;
		result.checkpointSha256 = r["checkpointSha256"].readVal<std::string>();
		if (result.checkpointSha256.size() != 64 || !std::all_of(result.checkpointSha256.begin(), result.checkpointSha256.end(),
			[](char c) { return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'); })) return result;
		const auto status = r["status"].readVal<std::string>();
		if (status != "PREDICTED" && status != "ABSTAIN" && status != "NO_ADMITTED_EVIDENCE" && status != "INPUT_LIMIT")
			return result;
		result.rawResponse = response;
		if (status == "NO_ADMITTED_EVIDENCE" || status == "INPUT_LIMIT")
		{
			result.status = status;
			return result;
		}
		double sum = 0;
		const auto probabilities = r["answer"]["probabilities"].children();
		if (probabilities.size() < 2 || probabilities.size() > AlienCommand::MAX_CANDIDATES + 1) return result;
		for (const auto &p : probabilities)
		{
			const double value = p.readVal<double>();
			if (!std::isfinite(value) || value < 0 || value > 1) return result;
			sum += value;
		}
		if (std::abs(sum - 1.0) > 0.01) return result;
		auto p = r["proposal"];
		result.proposal.mission = p["mission"].readVal<std::string>();
		result.proposal.region = p["region"].readVal<std::string>();
		result.proposal.reason = p["reason"].readVal<std::string>();
		result.proposal.score = p["score"].readVal<int>();
		p.readNode("evidenceIds", result.proposal.evidenceIds);
		if (status == "ABSTAIN")
		{
			if (!result.proposal.abstains() || result.proposal.score != 0 || !result.proposal.evidenceIds.empty()) return result;
			result.status = "MODEL_ABSTAIN";
		}
		else if (AlienCommand::validateProposal(input, result.proposal))
			result.status = "MODEL_PROPOSAL_VALID_SHADOW_ONLY";
		return result;
	}
	catch (const std::exception &)
	{
		return result;
	}
}

AlienCommandModelResult queryAlienReconModel(const AlienReconSnapshot &input, int port)
{
	AlienCommandModelResult result;
	if (port < 1 || port > 65535) { result.status = "INVALID_MODEL_PORT"; return result; }
	if (AlienCommand::chooseRecon(input).abstains()) { result.status = "NO_ADMITTED_EVIDENCE"; return result; }
	const auto body = AlienCommand::inputJson(input);
	if (body.size() > 32768) { result.status = "INPUT_LIMIT"; return result; }
 const auto response=queryAlienPortfolioTransport(body,port,L"/recon");
 if (response.empty()) { result.status="MODEL_UNAVAILABLE"; return result; }
 return validateAlienReconModelResponse(input,response);
}
std::string queryAlienPortfolioTransport(const std::string &body, int port, const wchar_t *endpoint)
{
 if (port < 1 || port > 65535 || body.size() > 32768) return "";
#ifdef _WIN32
	struct Handle
	{
		HINTERNET value = nullptr;
		~Handle() { if (value) WinHttpCloseHandle(value); }
	};
	
	Handle session{WinHttpOpen(L"OpenXcom alien command shadow", WINHTTP_ACCESS_TYPE_NO_PROXY,
		WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0)};
	if (!session.value || !WinHttpSetTimeouts(session.value, 500, 500, 1000,
  std::wstring(endpoint)==L"/portfolio" ? 45000 : 15000)) return "";
	Handle connection{WinHttpConnect(session.value, L"127.0.0.1", (INTERNET_PORT)port, 0)};
	if (!connection.value) return "";
	Handle request{WinHttpOpenRequest(connection.value, L"POST", endpoint, nullptr, WINHTTP_NO_REFERER,
		WINHTTP_DEFAULT_ACCEPT_TYPES, 0)};
	if (!request.value) return "";
	DWORD disable = WINHTTP_DISABLE_REDIRECTS;
	if (!WinHttpSetOption(request.value, WINHTTP_OPTION_DISABLE_FEATURE, &disable, sizeof(disable))) return "";
	if (!WinHttpSendRequest(request.value, L"Content-Type: application/json\r\n", (DWORD)-1L,
		(LPVOID)body.data(), (DWORD)body.size(), (DWORD)body.size(), 0)
		|| !WinHttpReceiveResponse(request.value, nullptr)) return "";
	DWORD status = 0, size = sizeof(status);
	if (!WinHttpQueryHeaders(request.value, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
		WINHTTP_HEADER_NAME_BY_INDEX, &status, &size, WINHTTP_NO_HEADER_INDEX) || status != 200) return "";
	std::string response;
	char buffer[4096];
	DWORD count = 0;
	while (true)
	{
		if (!WinHttpReadData(request.value, buffer, sizeof(buffer), &count)) return "";
		if (!count) break;
		response.append(buffer, count);
		if (response.size() > 65536) return "";
	}
	return response;
#else
	
	return "";
#endif
}
std::string queryAlienPortfolioModel(const std::string &body, int port)
{
 return queryAlienPortfolioTransport(body,port,L"/portfolio");
}
}
