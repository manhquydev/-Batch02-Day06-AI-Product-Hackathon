"""Unit tests for domain_guard module."""

import pytest

from src.core.domain_guard import (
    build_off_topic_result,
    has_movie_intent,
    is_clear_off_topic,
)


class TestHasMovieIntent:
    """Tests for has_movie_intent() function."""

    # --- Happy cases: movie intent detected ---
    def test_vietnamese_movie_request(self):
        """Vietnamese: 'Gợi ý phim buồn'"""
        assert has_movie_intent("Gợi ý phim buồn")

    def test_vietnamese_movie_intent_verb(self):
        """Vietnamese: 'Tôi muốn xem phim tối nay'"""
        assert has_movie_intent("Tôi muốn xem phim tối nay")

    def test_vietnamese_movie_trending(self):
        """Vietnamese: 'Phim trending tuần này'"""
        assert has_movie_intent("Phim trending tuần này")

    def test_english_movie_recommend(self):
        """English: 'recommend a movie'"""
        assert has_movie_intent("recommend a movie")

    def test_english_netflix_horror(self):
        """English: 'netflix horror film'"""
        assert has_movie_intent("netflix horror film")

    def test_english_compare_movies(self):
        """English: 'compare inception and interstellar'"""
        assert has_movie_intent("compare inception and interstellar")

    def test_known_movie_title_inception(self):
        """Known title: 'inception'"""
        assert has_movie_intent("inception")

    def test_known_movie_title_parasite(self):
        """Known title: 'parasite'"""
        assert has_movie_intent("parasite")

    def test_known_movie_title_get_out(self):
        """Known title: 'get out'"""
        assert has_movie_intent("get out")

    def test_mixed_language_movie(self):
        """Mixed Vietnamese-English: 'Xem Inception ở đâu?'"""
        assert has_movie_intent("Xem Inception ở đâu?")

    def test_movie_intent_with_accents(self):
        """Movie intent with Vietnamese accents: 'Gợi ý phim'"""
        assert has_movie_intent("Gợi ý phim")

    def test_movie_intent_case_insensitive(self):
        """Case insensitivity: 'RECOMMEND A MOVIE'"""
        assert has_movie_intent("RECOMMEND A MOVIE")

    def test_tmdb_mention(self):
        """TMDB keyword: 'tmdb search'"""
        assert has_movie_intent("tmdb search")

    def test_imdb_mention(self):
        """IMDB keyword: 'imdb rating'"""
        assert has_movie_intent("imdb rating")

    # --- Off-topic cases (blocked) ---
    def test_off_topic_weather_vietnamese(self):
        """Off-topic: 'Thời tiết hôm nay thế nào?'"""
        assert not has_movie_intent("Thời tiết hôm nay thế nào?")

    def test_off_topic_cooking(self):
        """Off-topic: 'Dạy tôi nấu phở'"""
        assert not has_movie_intent("Dạy tôi nấu phở")

    def test_off_topic_history(self):
        """Off-topic: 'Lịch sử Việt Nam'"""
        assert not has_movie_intent("Lịch sử Việt Nam")

    def test_off_topic_machine_learning(self):
        """Off-topic: 'What is machine learning?'"""
        assert not has_movie_intent("What is machine learning?")

    def test_empty_string(self):
        """Empty string → False (no intent)"""
        assert not has_movie_intent("")

    def test_whitespace_only(self):
        """Whitespace only → False"""
        assert not has_movie_intent("   ")

    def test_off_topic_cooking_no_movie_word(self):
        """Off-topic: 'Nấu phở ngon' (no movie word)"""
        assert not has_movie_intent("Nấu phở ngon")

    def test_off_topic_travel(self):
        """Off-topic: 'Đi du lịch Đà Lạt' (no movie word)"""
        assert not has_movie_intent("Đi du lịch Đà Lạt")

    # --- Edge cases ---
    def test_accented_movie_term_normalized(self):
        """Accented movie term gets normalized"""
        # "phim" with accent normalization
        assert has_movie_intent("phim")

    def test_multiple_whitespace_normalized(self):
        """Multiple whitespace is normalized"""
        assert has_movie_intent("phim  nghe noi   great")

    def test_very_long_off_topic_text(self):
        """Very long off-topic text"""
        long_text = "Lịch sử của Việt Nam là một câu chuyện lâu đời " * 10
        assert not has_movie_intent(long_text)

    def test_movie_term_in_long_text(self):
        """Movie term embedded in long text"""
        text = "Tôi đang học lịch sử nhưng tôi cũng thích xem phim " + "rất nhiều" * 20
        assert has_movie_intent(text)

    def test_series_keyword(self):
        """'series' keyword detected"""
        assert has_movie_intent("best series to watch")

    def test_streaming_keyword(self):
        """'streaming' keyword detected"""
        assert has_movie_intent("streaming service")

    def test_review_keyword(self):
        """'review' keyword detected"""
        assert has_movie_intent("movie review")

    def test_rating_keyword(self):
        """'rating' keyword detected"""
        assert has_movie_intent("what's the rating")


class TestIsClearOffTopic:
    """Tests for is_clear_off_topic() function."""

    def test_empty_string_not_off_topic(self):
        """Empty string is NOT off-topic (empty → no blocking)"""
        assert not is_clear_off_topic("")

    def test_whitespace_not_off_topic(self):
        """Whitespace only is NOT off-topic"""
        assert not is_clear_off_topic("   ")

    def test_clear_off_topic_weather(self):
        """Clear off-topic: 'Thời tiết hôm nay?'"""
        assert is_clear_off_topic("Thời tiết hôm nay?")

    def test_clear_off_topic_history(self):
        """Clear off-topic: 'Lịch sử Việt Nam'"""
        assert is_clear_off_topic("Lịch sử Việt Nam")

    def test_movie_intent_not_off_topic(self):
        """Movie intent: 'Gợi ý phim' is NOT off-topic"""
        assert not is_clear_off_topic("Gợi ý phim")

    def test_english_off_topic(self):
        """Off-topic in English: 'What is AI?'"""
        assert is_clear_off_topic("What is AI?")

    def test_off_topic_cooking(self):
        """Off-topic: 'Nấu phở'"""
        assert is_clear_off_topic("Nấu phở")


class TestBuildOffTopicResult:
    """Tests for build_off_topic_result() function."""

    def test_off_topic_result_shape(self):
        """Result has correct shape"""
        result = build_off_topic_result("Thời tiết")
        assert isinstance(result, dict)
        assert "answer" in result
        assert "trace" in result
        assert "steps" in result
        assert "usage" in result
        assert "latency_ms" in result
        assert "mode" in result

    def test_off_topic_mode_is_domain_guard(self):
        """Result mode is 'domain_guard'"""
        result = build_off_topic_result("Thời tiết")
        assert result["mode"] == "domain_guard"

    def test_off_topic_trace_is_empty(self):
        """Result trace is empty list"""
        result = build_off_topic_result("Thời tiết")
        assert result["trace"] == []

    def test_off_topic_steps_zero(self):
        """Result steps is 0"""
        result = build_off_topic_result("Thời tiết")
        assert result["steps"] == 0

    def test_off_topic_latency_zero(self):
        """Result latency_ms is 0"""
        result = build_off_topic_result("Thời tiết")
        assert result["latency_ms"] == 0

    def test_off_topic_usage_zeros(self):
        """Result usage has zero tokens"""
        result = build_off_topic_result("Thời tiết")
        usage = result["usage"]
        assert usage["prompt_tokens"] == 0
        assert usage["completion_tokens"] == 0
        assert usage["total_tokens"] == 0

    def test_off_topic_answer_contains_query(self):
        """Result answer contains the original query"""
        query = "Thời tiết hôm nay"
        result = build_off_topic_result(query)
        assert query in result["answer"]

    def test_off_topic_answer_in_vietnamese(self):
        """Result answer is in Vietnamese"""
        result = build_off_topic_result("Thời tiết")
        assert "phim" in result["answer"]
        assert "ngoài phạm vi" in result["answer"]

    def test_off_topic_answer_suggests_movie_rewording(self):
        """Result answer suggests movie-related rephrasing"""
        result = build_off_topic_result("Thời tiết")
        assert "gợi ý phim" in result["answer"] or "xem phim" in result["answer"]
