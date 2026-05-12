from modules import Database
import nextcord as discord
from nextcord.ext import commands
import os
import sys
import asyncio
import time
import random
import psutil
from datetime import timedelta
from dotenv import load_dotenv, find_dotenv
from pycolorise.colors import *

load_dotenv(find_dotenv(raise_error_if_not_found=True))

class Auth:
    TOKEN = os.getenv("TOKEN")
    COMMAND_PREFIX = os.getenv("COMMAND_PREFIX")
    FILENAME = os.getenv("FILENAME")

class EconomyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_command", None)
        super().__init__(*args, **kwargs)
        self.db = Database(Auth.FILENAME)
        self.start_time = time.time()
        self.commands_used = 0
        self._proc = psutil.Process()
        self._proc.cpu_percent(interval=None)  # prime the cpu sampler
        self._last_net = psutil.net_io_counters()
        self._last_net_time = time.time()

    async def setup_hook(self):
        print(Purple("\n=== BOT STARTING ==="))
        print(Blue(f"cogs/ contents: {os.listdir('./cogs') if os.path.exists('./cogs') else 'MISSING'}"))
        try:
            await self.db.bank.create_table()
            await self.db.inv.create_table()
            print(Green("✅ Database tables ready"))
        except Exception as e:
            print(Red(f"❌ Database setup failed: {e}"))
        print(Purple("=== BOT INIT FINISHED ===\n"))

    async def on_ready(self):
        print(Purple("\n=== ON_READY STARTED ==="))
        for file in os.listdir("./cogs"):
            if file.endswith(".py") and not file.startswith("__"):
                filename = file[:-3]
                ext = f"cogs.{filename}"
                if ext in self.extensions:
                    continue
                try:
                    self.load_extension(ext)
                    print(Blue(f"- {filename} ✅ "))
                except Exception as e:
                    print(Red(f"- {filename} ❌ ({e})"))

        await self.change_presence(status=discord.Status.online, activity=discord.Game("/chelp"))
        print(Cyan(f"{self.user.name} is online !"))
        print(Blue(f"Loaded cogs: {list(self.cogs.keys())}"))

        await self.sync_all_application_commands()
        print(Green("✅ Slash commands synced"))
        print(Purple("=== ON_READY FINISHED ===\n"))

        self.loop.create_task(self.live_status_task())
        self.loop.create_task(self.console_stats_task())

    async def live_status_task(self):
        statuses = [
            "🌿 Planting on Block 7",
            "🔥 Running from the feds",
            "🧪 Cooking in the trap",
            "🏚️ Building the empire",
            "🚨 Heat Level Rising...",
            "💼 Counting the books",
        ]
        while True:
            try:
                msg = random.choice(statuses + [f"💎 Kingpin Mode • {len(self.guilds)} servers"])
                await self.change_presence(status=discord.Status.online, activity=discord.Game(msg))
            except Exception:
                pass
            await asyncio.sleep(45)

    async def console_stats_task(self):
        """Print live CPU/RAM/network stats to the server console every 10 seconds."""
        while True:
            try:
                cpu = self._proc.cpu_percent(interval=None)
                mem_mb = self._proc.memory_info().rss / 1024 / 1024
                total_mb = psutil.virtual_memory().total / 1024 / 1024
                total_str = f"{total_mb/1024:.1f}GB" if total_mb >= 1024 else f"{total_mb:.0f}MB"

                now = time.time()
                cur = psutil.net_io_counters()
                elapsed = max(0.001, now - self._last_net_time)
                rx_kbs = (cur.bytes_recv - self._last_net.bytes_recv) / elapsed / 1024
                tx_kbs = (cur.bytes_sent - self._last_net.bytes_sent) / elapsed / 1024
                self._last_net = cur
                self._last_net_time = now

                uptime_s = int(time.time() - self.start_time)
                h, rem = divmod(uptime_s, 3600)
                m, s = divmod(rem, 60)
                uptime = f"{h:02d}:{m:02d}:{s:02d}"

                ts = time.strftime("%H:%M:%S")
                line = (
                    f"[{ts}] {Cyan('STATS')} "
                    f"{Green(f'CPU {cpu:5.1f}%')} • "
                    f"{Blue(f'RAM {mem_mb:.1f}MB/{total_str}')} • "
                    f"{Purple(f'⬇{rx_kbs:6.1f}KB/s')} {Purple(f'⬆{tx_kbs:6.1f}KB/s')} • "
                    f"{Cyan(f'guilds {len(self.guilds)}')} • "
                    f"{Cyan(f'cmds {self.commands_used}')} • "
                    f"{Cyan(f'up {uptime}')}"
                )
                print(line, flush=True)
            except Exception as e:
                print(Red(f"console stats task error: {e}"), flush=True)
            await asyncio.sleep(600)

def setup(client):
    pass
