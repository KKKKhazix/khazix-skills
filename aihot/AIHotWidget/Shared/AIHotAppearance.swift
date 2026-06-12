import SwiftUI

enum AIHotAppearance: String, CaseIterable, Identifiable, Codable, Sendable {
    case automatic
    case light
    case dark
    case transparent

    var id: String { rawValue }

    var title: String {
        switch self {
        case .automatic:
            return "自动"
        case .light:
            return "浅色"
        case .dark:
            return "深色"
        case .transparent:
            return "透明"
        }
    }

    var symbol: String {
        switch self {
        case .automatic:
            return "circle.lefthalf.filled"
        case .light:
            return "sun.max.fill"
        case .dark:
            return "moon.fill"
        case .transparent:
            return "square.dashed"
        }
    }

    var forcedColorScheme: ColorScheme? {
        switch self {
        case .light:
            return .light
        case .dark:
            return .dark
        case .automatic, .transparent:
            return nil
        }
    }

    func primaryColor(systemScheme: ColorScheme) -> Color {
        switch self {
        case .light:
            return Color(red: 0.08, green: 0.08, blue: 0.09)
        case .dark:
            return .white
        case .automatic, .transparent:
            return systemScheme == .dark ? .white : Color(red: 0.08, green: 0.08, blue: 0.09)
        }
    }

    func secondaryColor(systemScheme: ColorScheme) -> Color {
        switch self {
        case .light:
            return Color(red: 0.36, green: 0.36, blue: 0.39)
        case .dark:
            return Color(red: 0.62, green: 0.62, blue: 0.66)
        case .automatic, .transparent:
            return systemScheme == .dark
                ? Color(red: 0.62, green: 0.62, blue: 0.66)
                : Color(red: 0.36, green: 0.36, blue: 0.39)
        }
    }

    @ViewBuilder
    func background(systemScheme: ColorScheme) -> some View {
        switch self {
        case .light:
            Color(red: 0.96, green: 0.96, blue: 0.97)
        case .dark:
            Color(red: 0.065, green: 0.065, blue: 0.075)
        case .automatic:
            if systemScheme == .dark {
                Color(red: 0.065, green: 0.065, blue: 0.075)
            } else {
                Color(red: 0.96, green: 0.96, blue: 0.97)
            }
        case .transparent:
            Color.clear
        }
    }
}

struct AIHotColorSchemeModifier: ViewModifier {
    let appearance: AIHotAppearance

    @ViewBuilder
    func body(content: Content) -> some View {
        if let colorScheme = appearance.forcedColorScheme {
            content.environment(\.colorScheme, colorScheme)
        } else {
            content
        }
    }
}

