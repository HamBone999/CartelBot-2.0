#!/bin/bash
echo "🛑 Stopping CartelBot..."
screen -S cartelbot -X quit 2>/dev/null && echo "✅ CartelBot stopped." || echo "No running bot found."
