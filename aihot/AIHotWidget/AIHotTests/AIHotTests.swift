import XCTest
@testable import AIHot

final class AIHotTests: XCTestCase {
    func testParsesCurrentTopicsFromHomepageHTML() throws {
        let html = """
        <section aria-label="当前热点">
          <ol class="hot-topics-list">
            <li class="hot-topics-row">
              <span class="hot-topics-rank hot-topics-rank-1">1</span>
              <a class="hot-topics-link" href="https://example.com/a?x=1&amp;y=2"
                 title="Claude &amp; Gemini">Claude &amp; Gemini</a>
              <span class="hot-topics-srcs timeline-dup-hover">26<!-- --> 个信源</span>
              <span class="hot-topics-time">10小时前</span>
            </li>
            <li class="hot-topics-row">
              <span class="hot-topics-rank hot-topics-rank-2">2</span>
              <a class="hot-topics-link" href="https://example.com/b"
                 title="第二条热点">第二条热点</a>
              <span class="hot-topics-srcs timeline-dup-hover">9 个信源</span>
              <span class="hot-topics-time">5小时前</span>
            </li>
          </ol>
        </section>
        """

        let topics = try AICurrentTopicsParser.parse(html: html)

        XCTAssertEqual(topics.count, 2)
        XCTAssertEqual(topics[0].rank, 1)
        XCTAssertEqual(topics[0].title, "Claude & Gemini")
        XCTAssertEqual(topics[0].sourceCount, 26)
        XCTAssertEqual(
            topics[0].url.absoluteString,
            "https://example.com/a?x=1&y=2"
        )
    }

    func testFixturesRespectSixItemLimit() {
        XCTAssertLessThanOrEqual(HotspotFixtures.aiTopics.count, 6)
    }

    func testCacheModelsRoundTrip() throws {
        let data = try JSONEncoder.hotspot.encode(HotspotFixtures.aiTopics)
        let decoded = try JSONDecoder.hotspot.decode(
            [AICurrentTopic].self,
            from: data
        )

        XCTAssertEqual(decoded, HotspotFixtures.aiTopics)
    }
}
