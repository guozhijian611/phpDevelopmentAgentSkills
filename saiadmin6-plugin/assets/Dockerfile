FROM php:8.4-cli-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git unzip libpq-dev libcurl4-openssl-dev libzip-dev libicu-dev libonig-dev libxml2-dev libpng-dev libjpeg62-turbo-dev libfreetype6-dev \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j2 pdo_mysql pdo_pgsql bcmath pcntl sockets zip intl mbstring gd curl dom simplexml xml xmlreader xmlwriter \
 && pecl install redis && docker-php-ext-enable redis \
 && rm -rf /var/lib/apt/lists/*
COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer
WORKDIR /app/server
CMD ["php", "start.php", "start"]
