import dotenv
import os
import json
import urllib.parse
import urllib.request
import logging
from datetime import datetime
from agents import Agent, Runner, function_tool

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

dotenv.load_dotenv(override=True)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Configuration
LOW_SCORE = 0.5
LOW_PROB = 0.6
FALLBACK_MARKERS = {"i don't know", "not sure", "cannot answer"}
_last_alert_time = {}
ALERT_COOLDOWN = 300


# DEBUG: Check environment variables
def check_environment():
    """Verify Telegram credentials are loaded"""
    logger.info("=" * 60)
    logger.info("ENVIRONMENT CHECK")
    logger.info("=" * 60)
    logger.info(f"TELEGRAM_BOT_TOKEN exists: {bool(TELEGRAM_BOT_TOKEN)}")
    if TELEGRAM_BOT_TOKEN:
        logger.info(f"TELEGRAM_BOT_TOKEN length: {len(TELEGRAM_BOT_TOKEN)}")
        logger.info(f"TELEGRAM_BOT_TOKEN preview: {TELEGRAM_BOT_TOKEN[:10]}...")
    else:
        logger.error("❌ TELEGRAM_BOT_TOKEN is missing!")
    
    logger.info(f"TELEGRAM_CHAT_ID exists: {bool(TELEGRAM_CHAT_ID)}")
    if TELEGRAM_CHAT_ID:
        logger.info(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")
    else:
        logger.error("❌ TELEGRAM_CHAT_ID is missing!")
    logger.info("=" * 60)


@function_tool
def notify_telegram(title: str, body: str, silent: bool = False) -> dict:
    """
    Send a short alert message to my Telegram when the agent is unsure.
    """
    logger.debug(f"notify_telegram called with title='{title}', body length={len(body)}")
    
    # Check credentials
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN is not set")
        return {"error": "TELEGRAM_BOT_TOKEN not configured", "success": False}
    
    if not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_CHAT_ID is not set")
        return {"error": "TELEGRAM_CHAT_ID not configured", "success": False}
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    text = f"*{title}*\n{body}"
    
    logger.debug(f"Message text: {text[:100]}...")
    
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": bool(silent),
    }
    
    encoded = urllib.parse.urlencode(data).encode()
    logger.debug(f"Request URL: {url[:50]}...")
    logger.debug(f"Request data keys: {list(data.keys())}")
    
    try:
        logger.info(f"📤 Sending Telegram message...")
        with urllib.request.urlopen(url, data=encoded, timeout=10) as r:
            response = json.loads(r.read().decode())
            logger.info(f"✅ Telegram API response: {response}")
            return response
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        logger.error(f"❌ HTTP Error {e.code}: {error_body}")
        return {"error": f"HTTP {e.code}: {error_body}", "success": False}
    except urllib.error.URLError as e:
        logger.error(f"❌ URL Error: {e.reason}")
        return {"error": f"URL Error: {e.reason}", "success": False}
    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return {"error": str(e), "success": False}


def _should_alert(query: str) -> bool:
    """Check if we should send an alert for this query"""
    import time
    
    now = time.time()
    query_hash = hash(query)
    
    if query_hash in _last_alert_time:
        elapsed = now - _last_alert_time[query_hash]
        if elapsed < ALERT_COOLDOWN:
            logger.debug(f"⏭️  Skipping alert (cooldown: {elapsed:.0f}s < {ALERT_COOLDOWN}s)")
            return False
    
    _last_alert_time[query_hash] = now
    logger.debug(f"✅ Alert allowed for query")
    return True


def handle_turn(user_query: str, agent):
    """Handle a user query with detailed debugging"""
    logger.info("\n" + "=" * 60)
    logger.info(f"NEW QUERY: {user_query}")
    logger.info("=" * 60)
    
    # Get agent's response
    logger.debug("Calling agent.answer()...")
    result = agent.answer(user_query)
    text = result.text
    logger.info(f"Agent response preview: {text[:150]}...")
    
    # Extract confidence metrics
    low_conf = getattr(result, "confidence", None)
    top_score = getattr(result, "top_retrieval_score", None)
    
    logger.debug(f"Confidence: {low_conf}")
    logger.debug(f"Top retrieval score: {top_score}")
    
    # Check uncertainty indicators
    is_fallback_text = any(m in text.lower() for m in FALLBACK_MARKERS)
    logger.debug(f"Contains fallback markers: {is_fallback_text}")
    
    is_low_conf = (
        (top_score is not None and top_score < LOW_SCORE)
        or (low_conf is not None and low_conf < LOW_PROB)
    )
    logger.debug(f"Low confidence detected: {is_low_conf}")
    
    # Decision to alert
    should_alert = (is_fallback_text or is_low_conf)
    logger.info(f"Should alert: {should_alert}")
    
    if should_alert and _should_alert(user_query.strip().lower()):
        logger.info("📢 Triggering Telegram notification...")
        try:
            response = notify_telegram(
                title="🚨 Agent doesn't know",
                body=f"Query: {user_query}\nPreview: {text[:400]}",
                silent=False
            )
            if response.get("success") is False or "error" in response:
                logger.error(f"❌ Notification failed: {response}")
            else:
                logger.info(f"✅ Notification sent successfully!")
        except Exception as e:
            logger.exception(f"❌ Exception during notification: {e}")
    else:
        logger.info("ℹ️  No notification needed")
    
    logger.info("=" * 60 + "\n")
    return result


# ============================================================================
# DEBUGGING UTILITIES
# ============================================================================

def test_telegram_credentials():
    """Test if Telegram credentials work"""
    logger.info("\n" + "🧪 TESTING TELEGRAM CREDENTIALS")
    logger.info("=" * 60)
    
    check_environment()
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ Cannot test - credentials missing")
        return False
    
    logger.info("Attempting to send test message...")
    result = notify_telegram(
        title="🧪 Test Message",
        body=f"Test sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        silent=True
    )
    
    success = result.get("ok", False) if isinstance(result, dict) else False
    if success:
        logger.info("✅ TEST PASSED - Telegram is working!")
    else:
        logger.error(f"❌ TEST FAILED - {result}")
    
    return success


def test_agent_integration(agent):
    """Test the full integration with sample queries"""
    logger.info("\n" + "🧪 TESTING AGENT INTEGRATION")
    logger.info("=" * 60)
    
    test_queries = [
        "What is 2+2?",  # Should be confident
        "What is the meaning of life?",  # Might be uncertain
    ]
    
    for query in test_queries:
        logger.info(f"\n📝 Testing query: {query}")
        try:
            result = handle_turn(query, agent)
            logger.info(f"Response: {result.text[:100]}...")
        except Exception as e:
            logger.exception(f"❌ Error during test: {e}")


def debug_mode():
    """Run all debugging checks"""
    logger.info("\n" + "🐛 DEBUG MODE ACTIVATED")
    logger.info("=" * 60)
    
    # Check environment
    check_environment()
    
    # Test Telegram
    test_telegram_credentials()
    
    logger.info("\n✅ Debug checks complete!")


# ============================================================================
# MAIN USAGE
# ============================================================================

if __name__ == "__main__":
    # Run debugging first
    debug_mode()
    
    # Initialize agent (uncomment when ready)
    # agent = Agent(
    #     name='Twin',
    #     instructions="Your instructions here",
    #     tools=[notify_telegram]
    # )
    # 
    # # Test with agent
    # test_agent_integration(agent)
    # 
    # # Normal usage
    # result = handle_turn("What is Python?", agent)