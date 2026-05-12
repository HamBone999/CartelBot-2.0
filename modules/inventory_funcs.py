from .ext import execute

SHOP_CATEGORIES = {
    "cooking":  ("🧪", "Cooking Supplies"),
    "gear":     ("🔧", "Street Gear"),
    "weapons":  ("⚔️",  "Weapons"),
    "vehicles": ("🚗", "Vehicles"),
    "luxury":   ("💎", "Luxury & Flex"),
    "misc":     ("🎲", "Misc & Edgy"),
}

class Inventory:
    def __init__(self, db):
        self.db = db
        self.shop_items = [
            # ── Cooking Supplies ──────────────────────────────────────────
            {"id":  1, "name": "weed_seeds",       "cost":    300, "category": "cooking",  "info": "🌱 Basic weed seeds"},
            {"id":  2, "name": "coke_kit",          "cost":  1_200, "category": "cooking",  "info": "❄️ Cocaine production kit"},
            {"id":  3, "name": "meth",              "cost":  2_500, "category": "cooking",  "info": "💎 Meth production setup"},
            {"id":  4, "name": "battery",           "cost":    180, "category": "cooking",  "info": "🔋 Battery for cooking"},
            {"id":  5, "name": "pseudo",            "cost":    950, "category": "cooking",  "info": "💊 Pseudoephedrine pills"},
            {"id":  6, "name": "acetone",           "cost":    320, "category": "cooking",  "info": "🧪 Acetone solvent"},
            {"id":  7, "name": "sulfuric",          "cost":    480, "category": "cooking",  "info": "🧪 Sulfuric acid"},
            {"id":  8, "name": "red_phos",          "cost":  1_350, "category": "cooking",  "info": "🔥 Red phosphorus"},
            {"id":  9, "name": "coffee_filters",    "cost":     90, "category": "cooking",  "info": "☕ Coffee filters"},
            {"id": 10, "name": "scale",             "cost":    650, "category": "cooking",  "info": "⚖️ Digital scale"},
            {"id": 11, "name": "ziplock",           "cost":     65, "category": "cooking",  "info": "📦 Ziplock bags"},
            {"id": 12, "name": "lighter",           "cost":     45, "category": "cooking",  "info": "🔥 Lighter"},
            {"id": 13, "name": "gloves",            "cost":    140, "category": "cooking",  "info": "🧤 Nitrile gloves"},
            {"id": 14, "name": "muriatic",          "cost":    410, "category": "cooking",  "info": "🧪 Muriatic acid"},
            {"id": 15, "name": "iodine",            "cost":    780, "category": "cooking",  "info": "🧪 Iodine crystals"},
            {"id": 16, "name": "beaker",            "cost":    220, "category": "cooking",  "info": "🧫 Borosilicate glass beaker"},
            {"id": 17, "name": "bunsen_burner",     "cost":    500, "category": "cooking",  "info": "🔥 Precise heat source"},
            {"id": 18, "name": "gas_mask",          "cost":  1_800, "category": "cooking",  "info": "😷 Don't breathe that in"},
            # ── Street Gear ───────────────────────────────────────────────
            {"id": 19, "name": "ski_mask",          "cost":    600, "category": "gear",     "info": "🎭 Essential. Non-negotiable."},
            {"id": 20, "name": "bulletproof_vest",  "cost":  8_500, "category": "gear",     "info": "🦺 Keep the lead out"},
            {"id": 21, "name": "burner_phone",      "cost":  1_200, "category": "gear",     "info": "📱 Untraceable. Toss it after."},
            {"id": 22, "name": "police_scanner",    "cost":  3_500, "category": "gear",     "info": "📡 Know before they show"},
            {"id": 23, "name": "brass_knuckles",    "cost":    800, "category": "gear",     "info": "👊 Old school persuasion"},
            {"id": 24, "name": "stash_box",         "cost":  1_800, "category": "gear",     "info": "📦 Hide your product"},
            {"id": 25, "name": "duct_tape",         "cost":    200, "category": "gear",     "info": "🩹 A thousand uses. Don't ask."},
            {"id": 26, "name": "zip_ties",          "cost":    150, "category": "gear",     "info": "🔗 For... securing packages"},
            {"id": 27, "name": "walkie_talkie",     "cost":    950, "category": "gear",     "info": "📻 Coordinate the operation"},
            {"id": 28, "name": "night_vision",      "cost": 12_000, "category": "gear",     "info": "👁️ Own the dark"},
            {"id": 29, "name": "lockpick_set",      "cost":  2_200, "category": "gear",     "info": "🔓 Doors are just suggestions"},
            {"id": 30, "name": "handcuffs",         "cost":    750, "category": "gear",     "info": "⛓️ For your enemies. Or yourself. No judgment."},
            {"id": 31, "name": "body_bag",          "cost":  1_100, "category": "gear",     "info": "🛍️ Discreet. Roomy. Two sizes."},
            {"id": 71, "name": "padlock",           "cost":  1_500, "category": "gear",     "info": "🔒 Auto-protects your wallet from one rob attempt"},
            # ── Weapons ───────────────────────────────────────────────────
            {"id": 32, "name": "switchblade",       "cost":  1_500, "category": "weapons",  "info": "🔪 Click. Instant respect."},
            {"id": 33, "name": "crowbar",           "cost":  2_000, "category": "weapons",  "info": "🔧 Opens doors AND skulls"},
            {"id": 34, "name": "taser",             "cost":  3_000, "category": "weapons",  "info": "⚡ Non-lethal. Mostly."},
            {"id": 35, "name": "molotov",           "cost":  8_000, "category": "weapons",  "info": "🍾 Boom in a bottle"},
            {"id": 36, "name": "pipe_bomb",         "cost": 15_000, "category": "weapons",  "info": "💣 For when things get real"},
            {"id": 37, "name": "sawed_off",         "cost": 22_000, "category": "weapons",  "info": "🔫 Compact. Messy. Effective."},
            {"id": 38, "name": "janky_silencer",    "cost":  5_500, "category": "weapons",  "info": "🔇 Reduces noise 12%. It's fine."},
            {"id": 39, "name": "baseball_bat",      "cost":    900, "category": "weapons",  "info": "⚾ America's pastime. Repurposed."},
            {"id": 40, "name": "machete",           "cost":  3_800, "category": "weapons",  "info": "🪓 Versatile. Agricultural."},
            # ── Vehicles ──────────────────────────────────────────────────
            {"id": 41, "name": "stolen_bike",       "cost":  5_000, "category": "vehicles", "info": "🚲 Fast exits, no plates"},
            {"id": 42, "name": "beater_car",        "cost": 18_000, "category": "vehicles", "info": "🚗 Runs. Sometimes."},
            {"id": 43, "name": "getaway_van",       "cost": 35_000, "category": "vehicles", "info": "🚐 Tinted. Spacious. Ask no questions."},
            {"id": 44, "name": "lowrider",          "cost": 55_000, "category": "vehicles", "info": "🚙 Hydraulics and respect"},
            {"id": 45, "name": "speedboat",         "cost": 80_000, "category": "vehicles", "info": "🚤 For the maritime drug lord"},
            {"id": 46, "name": "dirt_bike",         "cost":  9_500, "category": "vehicles", "info": "🏍️ Off-road. Off-grid. Off you go."},
            {"id": 47, "name": "armored_suv",       "cost":120_000, "category": "vehicles", "info": "🛡️ El Chapo approved"},
            # ── Luxury & Flex ─────────────────────────────────────────────
            {"id": 48, "name": "fake_gold_chain",   "cost":  2_500, "category": "luxury",   "info": "📿 Looks expensive. It's not."},
            {"id": 49, "name": "designer_watch",    "cost": 15_000, "category": "luxury",   "info": "⌚ Drip or drown"},
            {"id": 50, "name": "diamond_grill",     "cost": 28_000, "category": "luxury",   "info": "💎 Say cheese... if you dare"},
            {"id": 51, "name": "fur_coat",          "cost": 20_000, "category": "luxury",   "info": "🧥 Kingpin starter pack"},
            {"id": 52, "name": "gold_toilet",       "cost":100_000, "category": "luxury",   "info": "🚽 You flush money. Literal flex."},
            {"id": 53, "name": "counterfeit_bills", "cost":  8_000, "category": "luxury",   "info": "💵 Feels real. Spends real."},
            {"id": 54, "name": "penthouse_key",     "cost": 75_000, "category": "luxury",   "info": "🗝️ Top floor. Don't ask who owns it."},
            {"id": 55, "name": "yacht_deed",        "cost":250_000, "category": "luxury",   "info": "⛵ Registered in a country that doesn't exist"},
            {"id": 56, "name": "stacks_of_cash",    "cost": 50_000, "category": "luxury",   "info": "💰 Just for the photo. Obviously."},
            # ── Misc & Edgy ───────────────────────────────────────────────
            {"id": 57, "name": "crackpipe",         "cost":    250, "category": "misc",     "info": "🪈 For your most loyal customers"},
            {"id": 58, "name": "rusty_spoon",       "cost":     50, "category": "misc",     "info": "🥄 Nobody asks about the rust."},
            {"id": 59, "name": "cartel_cookbook",   "cost":  3_000, "category": "misc",     "info": "📖 Grandma's secret recipes 🙂"},
            {"id": 60, "name": "rat_poison",        "cost":  3_500, "category": "misc",     "info": "☠️ For the rats in your crew"},
            {"id": 61, "name": "dirty_cop_badge",   "cost": 15_000, "category": "misc",     "info": "🪪 He's on the payroll. Probably."},
            {"id": 62, "name": "mystery_package",   "cost":  2_000, "category": "misc",     "info": "📫 You don't know. Neither do we."},
            {"id": 63, "name": "narco_prayer_candle","cost":   500, "category": "misc",     "info": "🕯️ Pray to the cartel saints"},
            {"id": 64, "name": "blood_money_case",  "cost": 75_000, "category": "misc",     "info": "💼 It's just business"},
            {"id": 65, "name": "sus_backpack",      "cost":  4_500, "category": "misc",     "info": "🎒 Heavy. Ticking. Don't open it."},
            {"id": 66, "name": "fake_passport",     "cost": 25_000, "category": "misc",     "info": "🛂 New name. New life. New you."},
            {"id": 67, "name": "bleach",            "cost":    300, "category": "misc",     "info": "🧴 Cleans surfaces. Cleans evidence."},
            {"id": 68, "name": "unmarked_envelope", "cost":  1_500, "category": "misc",     "info": "✉️ For the judge. Or the chief. Or both."},
            {"id": 69, "name": "snitch_list",       "cost":  5_000, "category": "misc",     "info": "📋 Names, addresses, habits. Be careful."},
            {"id": 70, "name": "burner_barrel",     "cost":    800, "category": "misc",     "info": "🛢️ Evidence goes in. Smoke comes out."},
        ]

    async def create_table(self):
        columns = ", ".join([f"{item['name']} INTEGER DEFAULT 0" for item in self.shop_items])
        await execute(self.db, f"CREATE TABLE IF NOT EXISTS inventory (user_id INTEGER PRIMARY KEY, {columns})")
        # Migrate: add any new columns that don't exist yet
        existing = await execute(self.db, "PRAGMA table_info(inventory)")
        existing_names = {row[1] for row in existing} if existing else set()
        for item in self.shop_items:
            if item["name"] not in existing_names:
                try:
                    await execute(self.db, f"ALTER TABLE inventory ADD COLUMN {item['name']} INTEGER DEFAULT 0")
                except Exception:
                    pass

    async def open_acc(self, user):
        await execute(self.db, "INSERT OR IGNORE INTO inventory (user_id) VALUES (?)", user.id)

    def _validate_item(self, item_name: str):
        valid = {item["name"] for item in self.shop_items}
        if item_name not in valid:
            raise ValueError(f"Unknown item: {item_name!r}")

    async def update_acc(self, user, amount: int, item_name: str):
        self._validate_item(item_name)
        await self.open_acc(user)
        await execute(self.db, f"UPDATE inventory SET {item_name} = MAX(0, {item_name} + ?) WHERE user_id = ?", amount, user.id)
        data = await execute(self.db, f"SELECT {item_name} FROM inventory WHERE user_id = ?", user.id)
        return data[0] if data else [0]

    async def reset_all_items(self, user):
        cols = ", ".join(f"{item['name']} = 0" for item in self.shop_items)
        await self.open_acc(user)
        await execute(self.db, f"UPDATE inventory SET {cols} WHERE user_id = ?", user.id)

    async def get_acc(self, user):
        await self.open_acc(user)
        data = await execute(self.db, "SELECT * FROM inventory WHERE user_id = ?", user.id)
        return data[0] if data else None

    async def get_qty(self, user, item_name: str) -> int:
        self._validate_item(item_name)
        await self.open_acc(user)
        data = await execute(self.db, f"SELECT {item_name} FROM inventory WHERE user_id = ?", user.id)
        return (data[0][0] or 0) if data else 0

    async def has_item(self, user, item_name: str) -> bool:
        return (await self.get_qty(user, item_name)) > 0

    async def consume(self, user, item_name: str, amount: int = 1) -> bool:
        """Try to consume `amount` of an item. Returns True if successful."""
        qty = await self.get_qty(user, item_name)
        if qty < amount:
            return False
        await self.update_acc(user, -amount, item_name)
        return True
