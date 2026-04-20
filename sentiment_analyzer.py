from transformers import pipeline
import re
import warnings

warnings.filterwarnings("ignore")


class SentimentAnalyzer:
    def __init__(self):
        """Initialize with a real 3-class sentiment model"""
        print("🔄 Loading 3-class sentiment model... (first time may take a while)")

        # Real 3-class model: negative / neutral / positive
        self.model = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment"
        )

        print("✅ 3-class sentiment model loaded successfully!")

    def clean_text(self, text):
        """Clean and preprocess text"""
        text = str(text)

        # Remove URLs
        text = re.sub(r"http\S+|www\S+", "", text)

        # Remove extra whitespace
        text = " ".join(text.split())

        return text

    def analyze(self, text):
        """
        Analyze sentiment using a real 3-class model.
        Returns:
            sentiment, positive_score, negative_score, neutral_score
        """
        clean_text = self.clean_text(text)

        if not clean_text or len(clean_text) < 3:
            return {
                "sentiment": "neutral",
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0
            }

        # Keep text reasonably short
        if len(clean_text) > 500:
            clean_text = clean_text[:500]

        try:
            # Ask pipeline for all class scores
            results = self.model(clean_text, top_k=None)

            # Convert list of {label, score} into a consistent dict
            scores = {
                "LABEL_0": 0.0,  # negative
                "LABEL_1": 0.0,  # neutral
                "LABEL_2": 0.0   # positive
            }

            for item in results:
                scores[item["label"]] = float(item["score"])

            negative_score = round(scores["LABEL_0"], 3)
            neutral_score = round(scores["LABEL_1"], 3)
            positive_score = round(scores["LABEL_2"], 3)

            # Pick highest score as sentiment
            max_label = max(
                [
                    ("negative", negative_score),
                    ("neutral", neutral_score),
                    ("positive", positive_score)
                ],
                key=lambda x: x[1]
            )[0]

            return {
                "sentiment": max_label,
                "positive_score": positive_score,
                "negative_score": negative_score,
                "neutral_score": neutral_score
            }

        except Exception as e:
            print(f"Error analyzing text: {e}")
            return {
                "sentiment": "neutral",
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0
            }

    def analyze_with_confidence_check(self, text):
        """
        Compatibility method for app.py
        Adds confidence and review flags expected by upload flow
        """
        result = self.analyze(text)

        confidence = max(
            result["positive_score"],
            result["negative_score"],
            result["neutral_score"]
        )

        result["confidence"] = round(confidence, 3)

        # Review if prediction is weak / ambiguous
        result["needs_review"] = confidence < 0.60

        return result

    def analyze_batch(self, texts):
        """Analyze multiple texts"""
        results = []
        for i, text in enumerate(texts):
            results.append(self.analyze(text))
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1} comments...")
        return results


# Test the analyzer
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()

    test_comments = [
        "This is amazing! I love it!",
        "Terrible experience, very disappointed",
        "It's okay, nothing special",
        "The website works as expected.",
        "Not bad at all, actually pretty impressive!"
    ]

    print("\n" + "=" * 60)
    print("TESTING 3-CLASS SENTIMENT MODEL")
    print("=" * 60)

    for comment in test_comments:
        result = analyzer.analyze(comment)

        sentiment_emoji = (
            "😊" if result["sentiment"] == "positive"
            else "😞" if result["sentiment"] == "negative"
            else "😐"
        )

        print(f"\n📝 Comment: {comment}")
        print(f"   Result: {sentiment_emoji} {result['sentiment'].upper()}")
        print(
            f"   Confidence: "
            f"{max(result['positive_score'], result['negative_score'], result['neutral_score']):.2%}"
        )
        print(
            f"   Scores: "
            f"+{result['positive_score']:.2f} | "
            f"-{result['negative_score']:.2f} | "
            f"={result['neutral_score']:.2f}"
        )
