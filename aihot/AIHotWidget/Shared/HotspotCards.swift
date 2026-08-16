import SwiftUI

struct AICurrentTopicsCard: View {
    let topics: [AICurrentTopic]
    let appearance: AIHotAppearance
    var isWidget = false
    var showsBackground = true

    @Environment(\.colorScheme) private var colorScheme

    private var displayedTopics: [AICurrentTopic] {
        Array((topics.isEmpty ? HotspotFixtures.aiTopics : topics).prefix(6))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: isWidget ? 11 : 14) {
            HStack(spacing: 8) {
                Text("🔥")
                    .font(.system(size: isWidget ? 18 : 22))
                Text("当前热点")
                    .font(.system(size: isWidget ? 22 : 27, weight: .heavy, design: .rounded))
                    .foregroundStyle(appearance.primaryColor(systemScheme: colorScheme))
                Spacer()
                Text("AI HOT")
                    .font(.system(size: isWidget ? 10 : 12, weight: .bold, design: .rounded))
                    .foregroundStyle(appearance.secondaryColor(systemScheme: colorScheme))
            }

            ForEach(displayedTopics) { topic in
                Link(destination: topic.url) {
                    HStack(alignment: .firstTextBaseline, spacing: 10) {
                        Text("\(topic.rank)")
                            .font(.system(size: isWidget ? 16 : 18, weight: .bold, design: .rounded))
                            .foregroundStyle(rankColor(topic.rank))
                            .frame(width: isWidget ? 21 : 24, alignment: .leading)

                        VStack(alignment: .leading, spacing: 3) {
                            Text(topic.title)
                                .font(.system(size: isWidget ? 14.5 : 17, weight: .bold))
                                .foregroundStyle(
                                    appearance.primaryColor(systemScheme: colorScheme)
                                )
                                .lineLimit(2)
                                .truncationMode(.tail)

                            HStack(spacing: 5) {
                                Text("\(topic.sourceCount) 个信源")
                                Text("•")
                                Text(topic.ageText)
                            }
                            .font(.system(size: isWidget ? 10.5 : 12.5, weight: .medium))
                            .foregroundStyle(
                                appearance.secondaryColor(systemScheme: colorScheme)
                            )
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .frame(maxHeight: .infinity, alignment: .center)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(
                    "第 \(topic.rank) 名，\(topic.title)，"
                        + "\(topic.sourceCount) 个信源，\(topic.ageText)"
                )
                .accessibilityHint("打开热点原始网页")
            }
        }
        .padding(isWidget ? 18 : 22)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .cardBackground(
            appearance: appearance,
            colorScheme: colorScheme,
            isWidget: isWidget,
            showsBackground: showsBackground
        )
    }

    private func rankColor(_ rank: Int) -> Color {
        switch rank {
        case 1:
            return .red
        case 2:
            return .yellow
        case 3:
            return .cyan
        default:
            return appearance.secondaryColor(systemScheme: colorScheme)
        }
    }
}

private extension View {
    func cardBackground(
        appearance: AIHotAppearance,
        colorScheme: ColorScheme,
        isWidget: Bool,
        showsBackground: Bool
    ) -> some View {
        background {
            if showsBackground {
                appearance.background(systemScheme: colorScheme)
            }
        }
        .clipShape(
            RoundedRectangle(cornerRadius: isWidget ? 0 : 30, style: .continuous)
        )
        .modifier(AIHotColorSchemeModifier(appearance: appearance))
    }
}
