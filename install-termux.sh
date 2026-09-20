#!/data/data/com.termux/files/usr/bin/bash
set -e
echo "[2DoArchive] Instalador para Termux"
pkg update -y
pkg install -y python
mkdir -p "$HOME/2DoArchive"
cp 2doarchive.py run.sh "$HOME/2DoArchive/"
chmod +x "$HOME/2DoArchive/run.sh"

BIN="$PREFIX/bin/archive"
cat > "$BIN" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
exec python3 "\$HOME/2DoArchive/2doarchive.py" "\$@"
EOF
chmod +x "$BIN"

echo
echo "✓ 2DoArchive instalado."
echo "Ahora puedes escribir:"
echo "  archive"
