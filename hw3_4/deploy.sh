

IMAGE_NAME_API="fastapi_parser"
CONTAINER_NAME_API="fastapi_parser_container"
CONTAINER_NAME_BD="db_postgres_container"

echo -e "\e[33m⏳ Останавливаем службу PostgreSQL...\e[0m"
sudo systemctl stop postgresql || {
    echo -e "\e[31m❌ Ошибка при остановке службы PostgreSQL.\e[0m"
    exit 1;
}
echo -e "\e[32m✅ Служба PostgreSQL успешно остановлена.\e[0m"

docker network inspect app-network >/dev/null 2>&1 || \
    docker network create app-network


if docker images -q "$IMAGE_NAME_API" | grep -q .; then
    echo -e "\e[32m✅ Образ $IMAGE_NAME_API существует.\e[0m"
else
    echo -e "\e[33m⏳ Образ $IMAGE_NAME_API не найден. Собираем образ...\e[0m"
    docker build -t "$IMAGE_NAME_API" .
fi

if docker ps -aq -f "name=$CONTAINER_NAME_BD" | grep -q .; then
    echo -e "\e[32m✅ Контейнер $CONTAINER_NAME_BD существует.\e[0m"
    if docker ps -q -f "name=$CONTAINER_NAME_BD" | grep -q .; then
        echo -e "\e[32m✅ Контейнер $CONTAINER_NAME_BD уже запущен.\e[0m"
    else
        echo -e "\e[33m⏳ Запуск контейнера $CONTAINER_NAME_BD...\e[0m"
        docker start "$CONTAINER_NAME_BD"
    fi
else
    echo -e "\e[33m⏳ Контейнер $CONTAINER_NAME_BD не существует. Создание и запуск...\e[0m"
    docker run -d \
        --name "$CONTAINER_NAME_BD" \
        --network app-network \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=12345 \
        -e POSTGRES_DB=la-rose_db \
        -p 5432:5432 \
        -v postgres-data:/var/lib/postgresql/data \
        postgres:latest
    echo -e "\e[32m⏳ Ожидаем запуск PostgreSQL (15 секунд)...\e[0m"
    sleep 15
fi


if docker ps -aq -f "name=$CONTAINER_NAME_API" | grep -q .; then
    echo -e "\e[32m✅ Контейнер $CONTAINER_NAME_API существует.\e[0m"
    if docker ps -q -f "name=$CONTAINER_NAME_API" | grep -q .; then
        echo -e "\e[32m✅ Контейнер $CONTAINER_NAME_API уже запущен.\e[0m"
    else
        echo -e "\e[33m⏳ Запуск контейнера $CONTAINER_NAME_API...\e[0m"
        docker start "$CONTAINER_NAME_API"
    fi
else
    echo -e "\e[33m⏳ Контейнер $CONTAINER_NAME_API не существует. Создание и запуск...\e[0m"
    docker run -d \
        --name "$CONTAINER_NAME_API" \
        -p 8000:8000 \
        --network app-network \
        "$IMAGE_NAME_API"
fi

echo -e "\e[32m✅ Состояние контейнеров:\e[0m"
docker ps --filter "name=$CONTAINER_NAME_API"
docker ps --filter "name=$CONTAINER_NAME_BD"
