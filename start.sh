#!/bin/bash
echo "🚀 Starting CartelBot..."
echo "══════════════════════════════════════════════════════════════"
echo "                  CARTELBOT STARTING UP                       "
echo "══════════════════════════════════════════════════════════════"
echo ""

# Kill old session if it exists
screen -S cartelbot -X quit 2>/dev/null || true

# Start the bot with live stats
screen -S cartelbot -dm bash -c "
    source venv/bin/activate
    echo '✅ CartelBot is now running!'
    echo 'Live stats will update every 45 seconds below...'
    echo ''
    python main.py
"

echo "✅ CartelBot started successfully!"
echo ""
echo "📌 Commands:"
echo "   screen -r cartelbot     → View bot + live stats"
echo "   ./stop.sh               → Stop the bot"
echo "   screen -ls              → Check running sessions"
