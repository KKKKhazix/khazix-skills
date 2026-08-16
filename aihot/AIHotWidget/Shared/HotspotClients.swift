import Foundation

private enum HotspotRequest {
    static let userAgent =
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        + "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
        + "Mobile/15E148 Safari/604.1 HotspotWidgets/1.0"

    static func make(url: URL, accept: String) -> URLRequest {
        var request = URLRequest(
            url: url,
            cachePolicy: .reloadRevalidatingCacheData,
            timeoutInterval: 15
        )
        request.setValue(userAgent, forHTTPHeaderField: "User-Agent")
        request.setValue(accept, forHTTPHeaderField: "Accept")
        return request
    }

    static func data(for request: URLRequest) async throws -> Data {
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse else {
            throw HotspotError.invalidResponse
        }
        guard 200..<300 ~= response.statusCode else {
            throw HotspotError.httpStatus(response.statusCode)
        }
        return data
    }
}

struct AICurrentTopicsClient: Sendable {
    static let pageURL = URL(string: "https://aihot.virxact.com/")!

    func fetchTopics() async throws -> [AICurrentTopic] {
        let request = HotspotRequest.make(url: Self.pageURL, accept: "text/html")
        let data = try await HotspotRequest.data(for: request)
        guard let html = String(data: data, encoding: .utf8) else {
            throw HotspotError.invalidText
        }
        return try AICurrentTopicsParser.parse(html: html)
    }
}

enum AICurrentTopicsParser {
    static func parse(html: String) throws -> [AICurrentTopic] {
        guard
            let listHTML = firstCapture(
                pattern: #"<ol class="hot-topics-list">(.*?)</ol>"#,
                in: html
            )
        else {
            throw HotspotError.missingCurrentTopics
        }

        let rows = captures(
            pattern: #"<li class="hot-topics-row">(.*?)</li>"#,
            in: listHTML
        )

        let topics = rows.prefix(6).compactMap { row -> AICurrentTopic? in
            guard
                let rankText = firstCapture(
                    pattern: #"hot-topics-rank[^"]*"[^>]*>(\d+)</span>"#,
                    in: row
                ),
                let rank = Int(rankText),
                let href = firstCapture(
                    pattern: #"<a class="hot-topics-link" href="([^"]+)""#,
                    in: row
                ),
                let title = firstCapture(
                    pattern: #"<a class="hot-topics-link"[^>]*title="([^"]+)""#,
                    in: row
                ),
                let url = URL(string: decodeHTMLEntities(href))
            else {
                return nil
            }

            let sourceCount = firstCapture(
                pattern: #"hot-topics-srcs timeline-dup-hover">(\d+)(?:<!-- -->)? 个信源"#,
                in: row
            ).flatMap(Int.init) ?? 0

            let ageText = firstCapture(
                pattern: #"hot-topics-time">([^<]+)</span>"#,
                in: row
            ).map(decodeHTMLEntities) ?? ""

            return AICurrentTopic(
                id: url.absoluteString,
                rank: rank,
                title: decodeHTMLEntities(title),
                url: url,
                sourceCount: sourceCount,
                ageText: ageText
            )
        }

        guard !topics.isEmpty else {
            throw HotspotError.missingCurrentTopics
        }
        return topics
    }

    private static func firstCapture(pattern: String, in text: String) -> String? {
        captures(pattern: pattern, in: text).first
    }

    private static func captures(pattern: String, in text: String) -> [String] {
        guard
            let expression = try? NSRegularExpression(
                pattern: pattern,
                options: [.dotMatchesLineSeparators]
            )
        else {
            return []
        }

        let range = NSRange(text.startIndex..., in: text)
        return expression.matches(in: text, range: range).compactMap { match in
            guard
                match.numberOfRanges > 1,
                let captureRange = Range(match.range(at: 1), in: text)
            else {
                return nil
            }
            return String(text[captureRange])
        }
    }

    private static func decodeHTMLEntities(_ text: String) -> String {
        var decoded = text
            .replacingOccurrences(of: "&amp;", with: "&")
            .replacingOccurrences(of: "&quot;", with: "\"")
            .replacingOccurrences(of: "&#39;", with: "'")
            .replacingOccurrences(of: "&lt;", with: "<")
            .replacingOccurrences(of: "&gt;", with: ">")

        let numericPattern = #"&#(x?[0-9A-Fa-f]+);"#
        guard let expression = try? NSRegularExpression(pattern: numericPattern) else {
            return decoded
        }

        let matches = expression.matches(
            in: decoded,
            range: NSRange(decoded.startIndex..., in: decoded)
        )

        for match in matches.reversed() {
            guard
                let fullRange = Range(match.range(at: 0), in: decoded),
                let valueRange = Range(match.range(at: 1), in: decoded)
            else {
                continue
            }

            let rawValue = String(decoded[valueRange])
            let radix = rawValue.hasPrefix("x") ? 16 : 10
            let digits = rawValue.hasPrefix("x") ? String(rawValue.dropFirst()) : rawValue
            guard
                let scalarValue = UInt32(digits, radix: radix),
                let scalar = UnicodeScalar(scalarValue)
            else {
                continue
            }
            decoded.replaceSubrange(fullRange, with: String(Character(scalar)))
        }

        return decoded
    }
}

enum HotspotError: LocalizedError {
    case invalidResponse
    case httpStatus(Int)
    case invalidText
    case missingCurrentTopics

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "服务器返回了无法识别的响应。"
        case let .httpStatus(status):
            return "服务器请求失败（HTTP \(status)）。"
        case .invalidText:
            return "热点页面编码无法识别。"
        case .missingCurrentTopics:
            return "没有在页面中找到“当前热点”。"
        }
    }
}

enum HotspotCache {
    private static let aiKey = "hotspots.ai.current"

    static func loadAITopics() -> [AICurrentTopic] {
        load([AICurrentTopic].self, key: aiKey) ?? []
    }

    static func saveAITopics(_ topics: [AICurrentTopic]) {
        save(topics, key: aiKey)
    }

    private static func load<Value: Decodable>(
        _ type: Value.Type,
        key: String
    ) -> Value? {
        guard let data = UserDefaults.standard.data(forKey: key) else {
            return nil
        }
        return try? JSONDecoder.hotspot.decode(type, from: data)
    }

    private static func save<Value: Encodable>(_ value: Value, key: String) {
        guard let data = try? JSONEncoder.hotspot.encode(value) else {
            return
        }
        UserDefaults.standard.set(data, forKey: key)
    }
}
