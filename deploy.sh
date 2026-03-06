#!/bin/bash
set -e

# ═══════════════════════════════════════════════════════════
#  ЗАПИСЬ.БОТ — Скрипт деплоя
#  Запуск: bash deploy.sh
# ═══════════════════════════════════════════════════════════

REPO_URL="https://github.com/ivanovilyavl/Lumilab.git"
INSTALL_DIR="/opt/zapisbot"
COMPOSE_FILE="docker-compose.prod.yml"

echo "══════════════════════════════════════"
echo "  ЗАПИСЬ.БОТ — Установка"
echo "══════════════════════════════════════"

# 1. Установка Docker (если нет)
if ! command -v docker &> /dev/null; then
    echo "📦 Устанавливаю Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker установлен"
else
    echo "✅ Docker уже установлен"
fi

# 2. Установка Docker Compose plugin (если нет)
if ! docker compose version &> /dev/null; then
    echo "📦 Устанавливаю Docker Compose..."
    apt-get update && apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose установлен"
else
    echo "✅ Docker Compose уже установлен"
fi

# 3. Установка Git (если нет)
if ! command -v git &> /dev/null; then
    echo "📦 Устанавливаю Git..."
    apt-get update && apt-get install -y git
fi

# 4. Клонирование / обновление репозитория
if [ -d "$INSTALL_DIR" ]; then
    echo "🔄 Обновляю репозиторий..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "📥 Клонирую репозиторий..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 5. Создание .env.prod если нет
if [ ! -f "$INSTALL_DIR/.env.prod" ]; then
    cp "$INSTALL_DIR/.env.prod.example" "$INSTALL_DIR/.env.prod"
    echo ""
    echo "⚠️  Создан файл .env.prod из примера."
    echo "    ОБЯЗАТЕЛЬНО заполни его перед запуском:"
    echo ""
    echo "    nano $INSTALL_DIR/.env.prod"
    echo ""
    echo "    Минимум нужно указать:"
    echo "    - BOT_TOKEN (из @BotFather)"
    echo "    - ANALYTICS_BOT_TOKEN (из @BotFather)"
    echo "    - ANALYTICS_ADMIN_IDS (твой Telegram ID)"
    echo "    - DB_PASSWORD (любой надёжный пароль)"
    echo "    - SECRET_KEY (случайная строка 32+ символов)"
    echo ""
    echo "    После заполнения запусти скрипт ещё раз."
    exit 0
fi

# 6. Проверяем что токены заполнены
source "$INSTALL_DIR/.env.prod"
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не заполнен в .env.prod!"
    echo "   nano $INSTALL_DIR/.env.prod"
    exit 1
fi

# 7. Сборка и запуск
echo "🔨 Собираю и запускаю контейнеры..."
cd "$INSTALL_DIR"
docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" up -d --build

# 8. Ждём пока БД поднимется
echo "⏳ Жду запуска базы данных..."
sleep 10

# 9. Миграции
echo "📊 Применяю миграции..."
docker compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head

echo ""
echo "══════════════════════════════════════"
echo "  ✅ ЗАПИСЬ.БОТ запущен!"
echo "══════════════════════════════════════"
echo ""
echo "  Проверить статус:  docker compose -f $COMPOSE_FILE ps"
echo "  Логи бота:         docker compose -f $COMPOSE_FILE logs -f bot"
echo "  Логи аналитики:    docker compose -f $COMPOSE_FILE logs -f analytics_bot"
echo "  Все логи:          docker compose -f $COMPOSE_FILE logs -f"
echo ""
