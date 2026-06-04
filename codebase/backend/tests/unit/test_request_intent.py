"""Unit tests for review vs detail intent detection."""

from src.utils.request_intent import (
    extract_target_movie_title,
    is_movie_detail_request,
    is_movie_review_request,
)


class TestMovieReviewIntent:
    def test_review_phrase_vi(self):
        assert is_movie_review_request("Cho mình xem review phim Inception")

    def test_danh_gia_phrase(self):
        assert is_movie_review_request("Đánh giá phim Parasite trên TMDB")

    def test_compare_not_review(self):
        assert not is_movie_review_request("So sánh Inception và Interstellar")

    def test_detail_not_review(self):
        assert is_movie_detail_request("Cho mình biết thêm về phim Inception")
        assert not is_movie_review_request("Cho mình biết thêm về phim Inception")

    def test_review_not_detail(self):
        assert is_movie_review_request("Review phim Inception")
        assert not is_movie_detail_request("Review phim Inception")

    def test_extract_title_from_review(self):
        title = extract_target_movie_title("Review phim Inception")
        assert title and "inception" in title.lower()
