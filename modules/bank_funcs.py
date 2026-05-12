from .ext import execute

# rank thresholds (XP needed for each rank)
RANK_THRESHOLDS = [0, 100, 500, 2000, 5000, 10000]  # Corner Boy → Kingpin
RANK_NAMES = ["Corner Boy", "Trap Star", "Lieutenant", "Capo", "Boss", "Kingpin"]
# rank perks: payout multiplier per rank
RANK_MULTIPLIERS = [1.00, 1.05, 1.10, 1.15, 1.25, 1.50]


def calc_rank(xp: int) -> int:
    """Return rank index 0-5 based on total XP."""
    rank = 0
    for i, threshold in enumerate(RANK_THRESHOLDS):
        if xp >= threshold:
            rank = i
    return rank


class Bank:
    def __init__(self, db):
        self.db = db

    async def create_table(self):
        await execute(self.db, """
            CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER PRIMARY KEY,
                wallet INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                heat INTEGER DEFAULT 0,
                rank INTEGER DEFAULT 0,
                gun TEXT DEFAULT 'none',
                crew TEXT DEFAULT NULL,
                territory TEXT DEFAULT NULL
            )
        """)
        await execute(self.db, """
            CREATE TABLE IF NOT EXISTS tycoon (
                user_id INTEGER PRIMARY KEY,
                houses INTEGER DEFAULT 1,
                level INTEGER DEFAULT 1
            )
        """)
        await execute(self.db, """
            CREATE TABLE IF NOT EXISTS plants (
                user_id INTEGER PRIMARY KEY,
                quantity INTEGER NOT NULL,
                planted_at INTEGER NOT NULL
            )
        """)
        # Migrate: add xp column if missing
        existing = await execute(self.db, "PRAGMA table_info(economy)")
        existing_names = {row[1] for row in existing} if existing else set()
        if "xp" not in existing_names:
            try:
                await execute(self.db, "ALTER TABLE economy ADD COLUMN xp INTEGER DEFAULT 0")
            except Exception:
                pass
        if "laylow_at" not in existing_names:
            try:
                await execute(self.db, "ALTER TABLE economy ADD COLUMN laylow_at INTEGER DEFAULT 0")
            except Exception:
                pass

    async def open_acc(self, user):
        await execute(self.db, "INSERT OR IGNORE INTO economy (user_id) VALUES (?)", user.id)

    async def get_acc(self, user):
        await self.open_acc(user)
        data = await execute(self.db, "SELECT wallet, bank, heat, rank, gun, crew, territory FROM economy WHERE user_id = ?", user.id)
        return [user.id] + list(data[0]) if data else None

    async def update_acc(self, user, amount, mode="wallet"):
        await self.open_acc(user)
        if mode == "heat":
            await execute(self.db, "UPDATE economy SET heat = heat + ? WHERE user_id = ?", amount, user.id)
        elif mode == "rank":
            await execute(self.db, "UPDATE economy SET rank = ? WHERE user_id = ?", amount, user.id)
        elif mode == "gun":
            await execute(self.db, "UPDATE economy SET gun = ? WHERE user_id = ?", amount, user.id)
        elif mode == "crew":
            await execute(self.db, "UPDATE economy SET crew = ? WHERE user_id = ?", amount, user.id)
        elif mode == "territory":
            await execute(self.db, "UPDATE economy SET territory = ? WHERE user_id = ?", amount, user.id)
        else:
            col = "wallet" if mode == "wallet" else "bank"
            # silently cap positive wallet additions
            if mode == "wallet" and isinstance(amount, int) and amount > 0:
                users = await self.get_acc(user)
                cap = await self.get_wallet_cap(user)
                space = max(0, cap - users[1])
                amount = min(amount, space)
            await execute(self.db, f"UPDATE economy SET {col} = {col} + ? WHERE user_id = ?", amount, user.id)

    async def get_wallet_cap(self, user) -> int:
        """Wallet cap = 50,000 base + 10,000 per trap house"""
        tycoon = await self.get_tycoon(user)
        houses = tycoon[0]
        return 50_000 + (houses - 1) * 10_000

    async def add_to_wallet(self, user, amount: int) -> tuple:
        """Add to wallet respecting cap. Returns (added, lost)."""
        if amount <= 0:
            return 0, 0
        await self.open_acc(user)
        users = await self.get_acc(user)
        cap = await self.get_wallet_cap(user)
        space = max(0, cap - users[1])
        added = min(amount, space)
        lost = amount - added
        if added > 0:
            await execute(self.db, "UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", added, user.id)
        return added, lost

    async def deposit(self, user, amount: int) -> int:
        """Move money from wallet to bank. Returns actual amount moved."""
        await self.open_acc(user)
        users = await self.get_acc(user)
        moved = min(amount, users[1])
        if moved > 0:
            await execute(self.db, "UPDATE economy SET wallet = wallet - ?, bank = bank + ? WHERE user_id = ?", moved, moved, user.id)
        return moved

    async def withdraw(self, user, amount: int) -> tuple:
        """Move money from bank to wallet (respects wallet cap). Returns (moved, lost_to_cap)."""
        await self.open_acc(user)
        users = await self.get_acc(user)
        cap = await self.get_wallet_cap(user)
        wallet_space = max(0, cap - users[1])
        moved = min(amount, users[2], wallet_space)
        if moved > 0:
            await execute(self.db, "UPDATE economy SET bank = bank - ?, wallet = wallet + ? WHERE user_id = ?", moved, moved, user.id)
        bank_short = max(0, amount - users[2])
        cap_short = max(0, amount - wallet_space) if amount <= users[2] else 0
        return moved, bank_short, cap_short

    async def reset_acc(self, user):
        await execute(self.db, "UPDATE economy SET wallet=0, bank=0, heat=0, rank=0, xp=0, gun='none', crew=NULL, territory=NULL WHERE user_id = ?", user.id)

    # ==================== XP / RANK ====================
    async def get_xp(self, user) -> int:
        await self.open_acc(user)
        data = await execute(self.db, "SELECT xp FROM economy WHERE user_id = ?", user.id)
        return (data[0][0] or 0) if data else 0

    async def award_xp(self, user, amount: int) -> tuple:
        """Add XP, recalculate rank. Returns (new_xp, new_rank, ranked_up)."""
        await self.open_acc(user)
        current = await self.get_xp(user)
        new_xp = current + amount
        old_rank = calc_rank(current)
        new_rank = calc_rank(new_xp)
        await execute(self.db, "UPDATE economy SET xp = ?, rank = ? WHERE user_id = ?", new_xp, new_rank, user.id)
        return new_xp, new_rank, new_rank > old_rank

    async def get_rank(self, user) -> int:
        await self.open_acc(user)
        users = await self.get_acc(user)
        return users[4] if users and len(users) > 4 else 0

    async def get_rank_multiplier(self, user) -> float:
        rank = await self.get_rank(user)
        return RANK_MULTIPLIERS[min(rank, 5)]

    # ==================== HEAT ====================
    async def get_heat(self, user) -> int:
        await self.open_acc(user)
        users = await self.get_acc(user)
        return users[3] if users and len(users) > 3 else 0

    async def set_heat(self, user, value: int):
        await self.open_acc(user)
        await execute(self.db, "UPDATE economy SET heat = MAX(0, ?) WHERE user_id = ?", value, user.id)

    async def reduce_heat(self, user, amount: int) -> int:
        await self.open_acc(user)
        heat = await self.get_heat(user)
        new = max(0, heat - amount)
        await execute(self.db, "UPDATE economy SET heat = ? WHERE user_id = ?", new, user.id)
        return heat - new

    async def get_laylow_at(self, user) -> int:
        data = await execute(self.db, "SELECT laylow_at FROM economy WHERE user_id = ?", user.id)
        return (data[0][0] or 0) if data else 0

    async def set_laylow_at(self, user, ts: int):
        await execute(self.db, "UPDATE economy SET laylow_at = ? WHERE user_id = ?", ts, user.id)

    async def get_tycoon(self, user):
        await execute(self.db, "INSERT OR IGNORE INTO tycoon (user_id) VALUES (?)", user.id)
        data = await execute(self.db, "SELECT houses, level FROM tycoon WHERE user_id = ?", user.id)
        return data[0] if data else (1, 1)

    async def update_tycoon(self, user, houses: int, level: int):
        await execute(self.db, "INSERT OR IGNORE INTO tycoon (user_id) VALUES (?)", user.id)
        await execute(self.db, "UPDATE tycoon SET houses = ?, level = ? WHERE user_id = ?", houses, level, user.id)

    async def get_plant(self, user):
        data = await execute(self.db, "SELECT quantity, planted_at FROM plants WHERE user_id = ?", user.id)
        return data[0] if data else None

    async def set_plant(self, user, quantity: int, planted_at: int):
        await execute(self.db, "INSERT OR REPLACE INTO plants (user_id, quantity, planted_at) VALUES (?, ?, ?)", user.id, quantity, planted_at)

    async def clear_plant(self, user):
        await execute(self.db, "DELETE FROM plants WHERE user_id = ?", user.id)

    async def crew_exists(self, name: str) -> bool:
        data = await execute(self.db, "SELECT 1 FROM economy WHERE crew = ? LIMIT 1", name)
        return bool(data)

    async def get_networth_lb(self):
        data = await execute(self.db, "SELECT user_id, (wallet + bank) as net FROM economy ORDER BY net DESC")
        return data or []
