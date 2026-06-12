import AppIntents
import SwiftUI
import WidgetKit

enum WidgetAppearanceOption: String, AppEnum {
    case automatic
    case light
    case dark
    case transparent

    static let typeDisplayRepresentation = TypeDisplayRepresentation(name: "外观")

    static let caseDisplayRepresentations: [Self: DisplayRepresentation] = [
        .automatic: "自动",
        .light: "浅色",
        .dark: "深色",
        .transparent: "透明",
    ]

    var appearance: AIHotAppearance {
        AIHotAppearance(rawValue: rawValue) ?? .automatic
    }
}

struct AICurrentTopicsConfigurationIntent: WidgetConfigurationIntent {
    static let title: LocalizedStringResource = "AI 当前热点外观"
    static let description = IntentDescription("选择 AI 当前热点小组件的外观。")

    @Parameter(title: "外观", default: .automatic)
    var appearance: WidgetAppearanceOption
}

struct AICurrentTopicsEntry: TimelineEntry {
    let date: Date
    let topics: [AICurrentTopic]
    let appearance: AIHotAppearance
    let isFallback: Bool
}

struct AICurrentTopicsProvider: AppIntentTimelineProvider {
    private let client = AICurrentTopicsClient()

    func placeholder(in context: Context) -> AICurrentTopicsEntry {
        AICurrentTopicsEntry(
            date: Date(),
            topics: HotspotFixtures.aiTopics,
            appearance: .dark,
            isFallback: false
        )
    }

    func snapshot(
        for configuration: AICurrentTopicsConfigurationIntent,
        in context: Context
    ) async -> AICurrentTopicsEntry {
        if context.isPreview {
            return AICurrentTopicsEntry(
                date: Date(),
                topics: HotspotFixtures.aiTopics,
                appearance: configuration.appearance.appearance,
                isFallback: false
            )
        }
        return await makeEntry(configuration)
    }

    func timeline(
        for configuration: AICurrentTopicsConfigurationIntent,
        in context: Context
    ) async -> Timeline<AICurrentTopicsEntry> {
        let entry = await makeEntry(configuration)
        return Timeline(entries: [entry], policy: .after(nextRefreshDate()))
    }

    private func makeEntry(
        _ configuration: AICurrentTopicsConfigurationIntent
    ) async -> AICurrentTopicsEntry {
        do {
            let topics = try await client.fetchTopics()
            HotspotCache.saveAITopics(topics)
            return AICurrentTopicsEntry(
                date: Date(),
                topics: topics,
                appearance: configuration.appearance.appearance,
                isFallback: false
            )
        } catch {
            let cached = HotspotCache.loadAITopics()
            return AICurrentTopicsEntry(
                date: Date(),
                topics: cached.isEmpty ? HotspotFixtures.aiTopics : cached,
                appearance: configuration.appearance.appearance,
                isFallback: true
            )
        }
    }
}

private func nextRefreshDate() -> Date {
    Calendar.current.date(byAdding: .minute, value: 15, to: Date())
        ?? Date().addingTimeInterval(15 * 60)
}

private struct FallbackIndicator: View {
    let isVisible: Bool
    let appearance: AIHotAppearance

    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        if isVisible {
            Image(systemName: "wifi.slash")
                .font(.caption2)
                .foregroundStyle(
                    appearance.secondaryColor(systemScheme: colorScheme)
                )
                .accessibilityLabel("当前显示缓存内容")
        }
    }
}

struct AICurrentTopicsWidgetView: View {
    let entry: AICurrentTopicsEntry

    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        AICurrentTopicsCard(
            topics: entry.topics,
            appearance: entry.appearance,
            isWidget: true,
            showsBackground: false
        )
        .overlay(alignment: .bottomTrailing) {
            FallbackIndicator(
                isVisible: entry.isFallback,
                appearance: entry.appearance
            )
            .padding(8)
        }
        .containerBackground(for: .widget) {
            entry.appearance.background(systemScheme: colorScheme)
        }
        .modifier(AIHotColorSchemeModifier(appearance: entry.appearance))
        .widgetURL(URL(string: "https://aihot.virxact.com/"))
    }
}

struct AICurrentTopicsWidget: Widget {
    let kind = "AICurrentTopicsWidget"

    var body: some WidgetConfiguration {
        AppIntentConfiguration(
            kind: kind,
            intent: AICurrentTopicsConfigurationIntent.self,
            provider: AICurrentTopicsProvider()
        ) { entry in
            AICurrentTopicsWidgetView(entry: entry)
        }
        .configurationDisplayName("AI 当前热点")
        .description("展示 AI HOT 当前聚合热点，最多 6 条。")
        .supportedFamilies([.systemLarge])
        .contentMarginsDisabled()
        .containerBackgroundRemovable(true)
    }
}

#Preview("AI 当前热点", as: .systemLarge) {
    AICurrentTopicsWidget()
} timeline: {
    AICurrentTopicsEntry(
        date: Date(),
        topics: HotspotFixtures.aiTopics,
        appearance: .dark,
        isFallback: false
    )
}
