import SwiftUI
import WidgetKit

struct ContentView: View {
    @State private var aiTopics = HotspotFixtures.aiTopics
    @State private var appearance = AIHotAppearance.automatic
    @State private var isLoading = false
    @State private var errorMessages: [String] = []

    private let aiClient = AICurrentTopicsClient()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    introduction
                    appearancePicker

                    sectionTitle("AI HOT 当前热点")
                    AICurrentTopicsCard(
                        topics: aiTopics,
                        appearance: appearance
                    )
                    .frame(minHeight: 390)
                    .cardShadow(appearance: appearance)

                    statusPanel
                    setupInstructions
                }
                .padding(.horizontal, 18)
                .padding(.bottom, 28)
            }
            .background(Color(uiColor: .systemGroupedBackground))
            .navigationTitle("热点小组件")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await refresh() }
                    } label: {
                        if isLoading {
                            ProgressView()
                        } else {
                            Label("刷新", systemImage: "arrow.clockwise")
                        }
                    }
                    .disabled(isLoading)
                }
            }
        }
        .task {
            await refresh()
        }
    }

    private var introduction: some View {
        VStack(alignment: .leading, spacing: 7) {
            Text("AI HOT 大号热点小组件")
                .font(.title2.bold())
            Text("将 AI HOT 当前热点以小组件形式展示在主屏幕，最多显示前 6 条。")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.top, 8)
    }

    private var appearancePicker: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("外观预览")
                .font(.headline)

            Picker("外观预览", selection: $appearance) {
                ForEach(AIHotAppearance.allCases) { option in
                    Label(option.title, systemImage: option.symbol)
                        .tag(option)
                }
            }
            .pickerStyle(.segmented)
        }
    }

    private func sectionTitle(_ title: String) -> some View {
        Text(title)
            .font(.headline)
    }

    @ViewBuilder
    private var statusPanel: some View {
        if errorMessages.isEmpty {
            Label(
                "已加载 \(aiTopics.count) 条 AI 当前热点",
                systemImage: "checkmark.circle.fill"
            )
            .font(.footnote)
            .foregroundStyle(.secondary)
        } else {
            VStack(alignment: .leading, spacing: 6) {
                ForEach(errorMessages, id: \.self) { message in
                    Label(message, systemImage: "exclamationmark.triangle.fill")
                }
            }
            .font(.footnote)
            .foregroundStyle(.orange)
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.orange.opacity(0.1), in: RoundedRectangle(cornerRadius: 16))
        }
    }

    private var setupInstructions: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("添加到主屏幕", systemImage: "plus.square.on.square")
                .font(.headline)

            Text("长按主屏幕 → 编辑 → 添加小组件，搜索“AI 当前热点”，选择大号尺寸。")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Text("长按小组件并选择“编辑小组件”，可切换自动、浅色、深色或透明外观。时间线每 15 分钟请求刷新，实际时刻由 iOS 调度。")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.background, in: RoundedRectangle(cornerRadius: 20))
    }

    @MainActor
    private func refresh() async {
        guard !isLoading else {
            return
        }

        isLoading = true
        errorMessages = []
        defer { isLoading = false }

        do {
            let topics = try await aiClient.fetchTopics()
            aiTopics = topics
            HotspotCache.saveAITopics(topics)
        } catch {
            let cached = HotspotCache.loadAITopics()
            if !cached.isEmpty {
                aiTopics = cached
            }
            errorMessages.append("AI 当前热点刷新失败，正在显示缓存。")
        }

        WidgetCenter.shared.reloadAllTimelines()
    }
}

private extension View {
    func cardShadow(appearance: AIHotAppearance) -> some View {
        shadow(
            color: .black.opacity(appearance == .transparent ? 0 : 0.16),
            radius: 24,
            y: 12
        )
    }
}

#Preview {
    ContentView()
}
