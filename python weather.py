# ============================================================
# SOVIT YADAV WEATHER AI BOT
# Developer: सुबित यादव
# Platform: Telegram
# Python: 3.10+
# ============================================================

import asyncio
import logging
import os
from datetime import datetime

import httpx
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

BOT_TOKEN = "8869527103:AAGxkZboJGBOd4K33oPT0y7xXy7kH9WKEl0"
WEATHER_API_KEY = "7122b39c593f55352dc00e89afd32d13"

# Optional: direct GIF URL for the /start animation.
# Leave empty to use the animated text welcome.
START_ANIMATION_URL = "https://giphy.com/gifs/wind-weather-miami-HmTLatwLWpTQk"

DEVELOPER = "SOVIT YADAV"
API_BASE = "https://api.openweathermap.org/data/2.5"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Simple weather icons
ICONS = {
    "clear": "☀️",
    "cloud": "☁️",
    "rain": "🌧️",
    "drizzle": "🌦️",
    "thunderstorm": "⛈️",
    "snow": "❄️",
    "mist": "🌫️",
    "fog": "🌫️",
    "haze": "🌫️",
    "smoke": "🌫️",
    "dust": "🌪️",
    "sand": "🌪️",
    "squall": "💨",
    "tornado": "🌪️",
}

# ================= KEYBOARDS =================

def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🌤️ Current Weather", "📅 5-Day Forecast"],
            ["🕒 Hourly Forecast", "🌫️ Air Quality"],
            ["🔍 Search City", "📍 Share Location"],
            ["🌡️ Change Units", "ℹ️ About Bot"],
            ["🔄 Refresh Weather", "❓ Help"],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Choose a weather feature...",
    )


def weather_inline_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Refresh", callback_data="refresh"
            ),
            InlineKeyboardButton(
                "📅 Forecast", callback_data="forecast"
            ),
        ],
        [
            InlineKeyboardButton(
                "🌫️ Air Quality", callback_data="air"
            ),
            InlineKeyboardButton(
                "🌡️ Change Units", callback_data="units"
            ),
        ],
    ])


def units_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "°C Celsius", callback_data="unit_C"
            ),
            InlineKeyboardButton(
                "°F Fahrenheit", callback_data="unit_F"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 Back", callback_data="refresh"
            )
        ],
    ])


# ================= API HELPERS =================

async def api_get(endpoint, params):
    params = dict(params)
    params["appid"] = WEATHER_API_KEY

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"{API_BASE}/{endpoint}",
            params=params,
        )

        if response.status_code == 404:
            raise ValueError("CITY_NOT_FOUND")

        response.raise_for_status()
        return response.json()


def temp_unit(context):
    return context.user_data.get("units", "metric")


def temp_symbol(context):
    return "°F" if temp_unit(context) == "imperial" else "°C"


def weather_icon(description):
    description = description.lower()

    for word, icon in ICONS.items():
        if word in description:
            return icon

    return "🌍"


def wind_unit(context):
    return "mph" if temp_unit(context) == "imperial" else "m/s"


def format_time(timestamp, timezone_offset=0):
    # OpenWeatherMap timezone is an offset from UTC.
    from datetime import timezone, timedelta

    dt = datetime.fromtimestamp(
        timestamp, tz=timezone.utc
    ) + timedelta(seconds=timezone_offset)

    return dt.strftime("%I:%M %p")


async def animated_message(message, final_text, **kwargs):
    """Small loading animation using editable Telegram text."""
    try:
        status = await message.reply_text("⏳ Connecting to weather satellite...")
        await asyncio.sleep(0.25)
        await status.edit_text("🌍 Fetching live weather data...")
        await asyncio.sleep(0.25)
        await status.edit_text("📡 Processing atmospheric information...")
        await asyncio.sleep(0.25)
        await status.edit_text(final_text, **kwargs)
        return status
    except Exception:
        return await message.reply_text(final_text, **kwargs)


async def get_current(city, context):
    return await api_get(
        "weather",
        {
            "q": city,
            "units": temp_unit(context),
        },
    )


async def get_forecast(city, context):
    return await api_get(
        "forecast",
        {
            "q": city,
            "units": temp_unit(context),
        },
    )


async def get_air_quality(lat, lon):
    return await api_get(
        "air_pollution",
        {
            "lat": lat,
            "lon": lon,
        },
    )


# ================= WEATHER FORMATTING =================

def current_weather_text(data, context):
    name = data["name"]
    country = data.get("sys", {}).get("country", "")
    weather = data["weather"][0]
    desc = weather["description"].title()
    icon = weather_icon(desc)
    main = data["main"]
    wind = data.get("wind", {})
    symbol = temp_symbol(context)

    feels = round(main.get("feels_like", 0))
    temp = round(main.get("temp", 0))
    humidity = main.get("humidity", 0)
    pressure = main.get("pressure", 0)
    wind_speed = wind.get("speed", 0)
    visibility = data.get("visibility", 0) / 1000
    sunrise = format_time(data["sys"]["sunrise"], data.get("timezone", 0))
    sunset = format_time(data["sys"]["sunset"], data.get("timezone", 0))

    return (
        f"╔════════════════════╗\n"
        f"   🌦️ SOVIT WEATHER AI\n"
        f"╚════════════════════╝\n\n"
        f"📍 Location: {name}, {country}\n"
        f"{icon} Condition: {desc}\n\n"
        f"🌡️ Temperature: {temp}{symbol}\n"
        f"🤗 Feels Like: {feels}{symbol}\n"
        f"💧 Humidity: {humidity}%\n"
        f"🌬️ Wind: {wind_speed} {wind_unit(context)}\n"
        f"🔵 Pressure: {pressure} hPa\n"
        f"👁️ Visibility: {visibility:.1f} km\n\n"
        f"🌅 Sunrise: {sunrise}\n"
        f"🌇 Sunset: {sunset}\n\n"
        f"🕒 Updated: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👨‍💻 Developer: {DEVELOPER}"
    )


def forecast_text(data, context, hourly=False):
    city = data["city"]["name"]
    symbol = temp_symbol(context)
    items = data.get("list", [])

    if hourly:
        items = items[:8]
        title = "🕒 NEXT 24 HOURS"
    else:
        # One entry around midday for each forecast day.
        selected = {}
        for item in items:
            date = item["dt_txt"][:10]
            hour = int(item["dt_txt"][11:13])

            if 11 <= hour <= 14 and date not in selected:
                selected[date] = item

        items = list(selected.values())[:5]
        title = "📅 5-DAY FORECAST"

    lines = [
        f"🌦️ SOVIT WEATHER AI",
        f"📍 {city}",
        f"━━━━━━━━━━━━━━━━━━━━",
        title,
        "",
    ]

    for item in items:
        date_text = item["dt_txt"]
        desc = item["weather"][0]["description"].title()
        icon = weather_icon(desc)
        temp = round(item["main"]["temp"])
        feels = round(item["main"]["feels_like"])
        humidity = item["main"]["humidity"]

        lines.append(
            f"{icon} {date_text}\n"
            f"   🌡️ {temp}{symbol} | 🤗 Feels {feels}{symbol}\n"
            f"   💧 Humidity {humidity}% | {desc}\n"
        )

    if len(lines) == 5:
        lines.append(
            "Forecast data is temporarily unavailable."
        )

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━",
        f"👨‍💻 Developer: {DEVELOPER}",
    ])

    return "\n".join(lines)


def air_quality_text(data):
    entry = data["list"][0]
    components = entry.get("components", {})
    aqi = entry["main"]["aqi"]

    levels = {
        1: "Good 🟢",
        2: "Fair 🟡",
        3: "Moderate 🟠",
        4: "Poor 🔴",
        5: "Very Poor 🟣",
    }

    return (
        "🌫️ AIR QUALITY REPORT\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 AQI: {aqi}/5\n"
        f"Status: {levels.get(aqi, 'Unknown')}\n\n"
        f"🫧 PM2.5: {components.get('pm2_5', 'N/A')} µg/m³\n"
        f"🌪️ PM10: {components.get('pm10', 'N/A')} µg/m³\n"
        f"💨 CO: {components.get('co', 'N/A')} µg/m³\n"
        f"🧪 NO₂: {components.get('no2', 'N/A')} µg/m³\n\n"
        "Note: AQI is reported on the API's 1–5 scale.\n"
        "👨‍💻 Developer: " + DEVELOPER
    )


# ================= CORE HANDLERS =================

async def show_weather(update, context, city=None, edit=False):
    city = city or context.user_data.get("city", "Delhi")

    if edit:
        target = update.callback_query.message
        await update.callback_query.answer()
        try:
            await target.edit_text("⏳ Fetching live weather...")
        except Exception:
            pass
    else:
        target = update.effective_message

    try:
        data = await get_current(city, context)
        context.user_data["city"] = data["name"]

        text = current_weather_text(data, context)

        if edit:
            await target.edit_text(
                text,
                reply_markup=weather_inline_keyboard(),
            )
        else:
            await animated_message(
                target,
                text,
                reply_markup=weather_inline_keyboard(),
            )

    except ValueError as exc:
        if str(exc) == "CITY_NOT_FOUND":
            await target.reply_text(
                "❌ City not found. Please check the spelling."
            )
        else:
            await target.reply_text("❌ Invalid city or API response.")
    except httpx.HTTPStatusError as exc:
        logger.warning("Weather API error: %s", exc)
        await target.reply_text(
            "⚠️ Weather API error. Check your API key and usage limits."
        )
    except Exception:
        logger.exception("Current weather error")
        await target.reply_text(
            "⚠️ Something went wrong. Please try again."
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("city", "Delhi")
    context.user_data.setdefault("units", "metric")

    welcome = (
        "✨ WELCOME TO SOVIT WEATHER AI ✨\n\n"
        "🌍 Your smart weather assistant!\n"
        "🌤️ Live weather and temperature\n"
        "📅 5-day forecast\n"
        "🕒 Hourly forecast\n"
        "🌫️ Air quality information\n"
        "📍 Weather by shared location\n\n"
        f"👨‍💻 Developer: {DEVELOPER}\n\n"
        "👇 Choose a feature from the keyboard!"
    )

    if START_ANIMATION_URL:
        try:
            await update.effective_message.reply_animation(
                animation=START_ANIMATION_URL,
                caption=welcome,
                reply_markup=main_keyboard(),
            )
            return
        except Exception:
            logger.warning("Start animation failed; using text.")

    await animated_message(
        update.effective_message,
        welcome,
        reply_markup=main_keyboard(),
    )


async def help_command(update: Update, context):
    await update.effective_message.reply_text(
        "❓ WEATHER BOT HELP\n\n"
        "🌤️ Current Weather — live conditions\n"
        "📅 5-Day Forecast — upcoming days\n"
        "🕒 Hourly Forecast — next 24 hours\n"
        "🌫️ Air Quality — pollution data\n"
        "🔍 Search City — find another city\n"
        "📍 Share Location — weather near you\n"
        "🌡️ Change Units — Celsius/Fahrenheit\n"
        "🔄 Refresh Weather — update the report\n\n"
        "You can also send a city name directly.\n"
        f"👨‍💻 Developer: {DEVELOPER}",
        reply_markup=main_keyboard(),
    )


async def about_command(update: Update, context):
    await update.effective_message.reply_text(
        "🌦️ SOVIT WEATHER AI BOT\n\n"
        "Built with Python and Telegram Bot API.\n"
        "Data provider: OpenWeatherMap\n"
        "Features: Current weather, forecast, AQI,\n"
        "location search and unit preferences.\n\n"
        f"Developer: {DEVELOPER}",
        reply_markup=main_keyboard(),
    )


async def send_forecast(update, context, hourly=False, edit=False):
    city = context.user_data.get("city", "Delhi")
    target = (
        update.callback_query.message
        if edit
        else update.effective_message
    )

    if edit:
        await update.callback_query.answer()
        try:
            await target.edit_text("⏳ Preparing forecast...")
        except Exception:
            pass

    try:
        data = await get_forecast(city, context)
        report = forecast_text(data, context, hourly=hourly)

        if edit:
            await target.edit_text(
                report,
                reply_markup=weather_inline_keyboard(),
            )
        else:
            await animated_message(
                target,
                report,
                reply_markup=weather_inline_keyboard(),
            )
    except Exception:
        logger.exception("Forecast error")
        await target.reply_text(
            "⚠️ Forecast unavailable. Check the city and API."
        )


async def send_air_quality(update, context, lat=None, lon=None):
    try:
        if lat is None or lon is None:
            city = context.user_data.get("city", "Delhi")
            current = await get_current(city, context)
            lat = current["coord"]["lat"]
            lon = current["coord"]["lon"]

        data = await get_air_quality(lat, lon)
        await animated_message(
            update.effective_message,
            air_quality_text(data),
            reply_markup=main_keyboard(),
        )
    except Exception:
        logger.exception("Air quality error")
        await update.effective_message.reply_text(
            "⚠️ Air quality data is unavailable right now."
        )


# ================= LOCATION & CITY SEARCH =================

async def receive_location(update: Update, context):
    location = update.effective_message.location

    try:
        current = await api_get(
            "weather",
            {
                "lat": location.latitude,
                "lon": location.longitude,
                "units": temp_unit(context),
            },
        )

        context.user_data["city"] = current["name"]

        await animated_message(
            update.effective_message,
            current_weather_text(current, context),
            reply_markup=weather_inline_keyboard(),
        )
    except Exception:
        logger.exception("Location weather error")
        await update.effective_message.reply_text(
            "⚠️ Couldn't retrieve weather for that location."
        )


async def handle_text(update: Update, context):
    text = update.effective_message.text.strip()

    if text == "🌤️ Current Weather":
        await show_weather(update, context)

    elif text == "📅 5-Day Forecast":
        await send_forecast(update, context)

    elif text == "🕒 Hourly Forecast":
        await send_forecast(update, context, hourly=True)

    elif text == "🌫️ Air Quality":
        await send_air_quality(update, context)

    elif text == "🔍 Search City":
        context.user_data["awaiting_city"] = True
        await update.effective_message.reply_text(
            "🔎 Send the city name now.\nExample: Mumbai"
        )

    elif text == "📍 Share Location":
        await update.effective_message.reply_text(
            "Tap the location button below to share your location.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(
                    "📍 Send My Location",
                    request_location=True,
                )], ["🔙 Back"]],
                resize_keyboard=True,
            ),
        )

    elif text == "🌡️ Change Units":
        await update.effective_message.reply_text(
            "Choose your preferred temperature unit:",
            reply_markup=units_keyboard(),
        )

    elif text == "ℹ️ About Bot":
        await about_command(update, context)

    elif text == "🔄 Refresh Weather":
        await show_weather(update, context)

    elif text == "❓ Help":
        await help_command(update, context)

    elif text == "🔙 Back":
        await update.effective_message.reply_text(
            "Main menu 👇",
            reply_markup=main_keyboard(),
        )

    elif context.user_data.pop("awaiting_city", False):
        context.user_data["city"] = text
        await show_weather(update, context, city=text)

    else:
        # Any other text is treated as a city name.
        await show_weather(update, context, city=text)


# ================= INLINE BUTTONS =================

async def inline_handler(update: Update, context):
    query = update.callback_query
    action = query.data

    if action == "refresh":
        await show_weather(update, context, edit=True)

    elif action == "forecast":
        await send_forecast(update, context, edit=True)

    elif action == "air":
        await query.answer()
        city = context.user_data.get("city", "Delhi")

        try:
            current = await get_current(city, context)
            data = await get_air_quality(
                current["coord"]["lat"],
                current["coord"]["lon"],
            )
            await query.message.reply_text(
                air_quality_text(data),
                reply_markup=weather_inline_keyboard(),
            )
        except Exception:
            logger.exception("Inline AQI error")
            await query.message.reply_text(
                "⚠️ Air quality data unavailable."
            )

    elif action == "units":
        await query.answer()
        await query.message.reply_text(
            "Choose temperature units:",
            reply_markup=units_keyboard(),
        )

    elif action in ("unit_C", "unit_F"):
        context.user_data["units"] = (
            "metric" if action == "unit_C" else "imperial"
        )
        await query.answer("Temperature unit updated!")
        await show_weather(update, context, edit=True)


# ================= ERROR HANDLER =================

async def error_handler(update, context):
    logger.error(
        "Unhandled exception",
        exc_info=context.error,
    )


# ================= MAIN =================

def main():
    if (
        BOT_TOKEN == "PASTE_TELEGRAM_BOT_TOKEN_HERE"
        or WEATHER_API_KEY == "PASTE_WEATHER_API_KEY_HERE"
    ):
        raise RuntimeError(
            "Please add your Telegram token and Weather API key in CONFIG."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))

    app.add_handler(CallbackQueryHandler(inline_handler))

    app.add_handler(
        MessageHandler(
            filters.LOCATION,
            receive_location,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text,
        )
    )

    app.add_error_handler(error_handler)

    logger.info("Sovit Weather AI Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()