import Foundation

struct AICurrentTopic: Codable, Identifiable, Hashable, Sendable {
    let id: String
    let rank: Int
    let title: String
    let url: URL
    let sourceCount: Int
    let ageText: String
}

extension JSONDecoder {
    static var hotspot: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .millisecondsSince1970
        return decoder
    }
}

extension JSONEncoder {
    static var hotspot: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .millisecondsSince1970
        return encoder
    }
}

extension Date {
    var compactRelativeText: String {
        let elapsed = Date().timeIntervalSince(self)
        if elapsed < 60 {
            return "刚刚"
        }

        let formatter = RelativeDateTimeFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: self, relativeTo: Date())
    }
}

enum HotspotFixtures {
    static let aiTopics: [AICurrentTopic] = [
        aiTopic(
            rank: 1,
            title: "Claude Fable 5 和 Claude Mythos 5",
            sourceCount: 26,
            ageText: "10小时前"
        ),
        aiTopic(
            rank: 2,
            title: "DiffusionGemma：文本生成速度提升4倍的开源扩散模型",
            sourceCount: 9,
            ageText: "5小时前"
        ),
        aiTopic(
            rank: 3,
            title: "小米发布并开源终端 AI 编程助手 MiMo Code V0.1.0",
            sourceCount: 4,
            ageText: "3小时前"
        ),
        aiTopic(
            rank: 4,
            title: "Anthropic CEO 呼吁缩小 AI 政策差距",
            sourceCount: 4,
            ageText: "5小时前"
        ),
        aiTopic(
            rank: 5,
            title: "Gemini Live Translate 发布",
            sourceCount: 10,
            ageText: "1天前"
        ),
    ]

    private static func aiTopic(
        rank: Int,
        title: String,
        sourceCount: Int,
        ageText: String
    ) -> AICurrentTopic {
        AICurrentTopic(
            id: "ai-\(rank)",
            rank: rank,
            title: title,
            url: URL(string: "https://aihot.virxact.com")!,
            sourceCount: sourceCount,
            ageText: ageText
        )
    }
}
