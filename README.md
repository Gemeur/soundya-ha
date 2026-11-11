# 🏠 Soundya для Home Assistant (Яндекс Станция 2)

[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom_Repo-orange.svg)](https://hacs.xyz/)
[![GitHub Release](https://img.shields.io/github/v/release/Gemeur/soundya-ha?include_prereleases&color=blue)](https://github.com/Gemeur/soundya-ha/releases)
[![Home Assistant](https://img.shields.io/badge/Home_Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)

Нативная интеграция прошивки **Soundya** и подсветки **Lumya** для Home Assistant. Работает напрямую по локальной сети через быстрый REST API без брокеров MQTT.

---

## ⚡ Установка через HACS (в 1 клик)

Нажмите кнопку ниже, чтобы автоматически добавить репозиторий в ваш Home Assistant:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Gemeur&repository=soundya-ha&category=integration)

### Или вручную через HACS:
1. Откройте **HACS** в Home Assistant $\to$ раздел **«Интеграции»**.
2. В верхнем правом углу нажмите меню из трёх точек $\to$ **«Пользовательские репозитории»** (*Custom repositories*).
3. Вставьте ссылку на репозиторий:  
   `https://github.com/Gemeur/soundya-ha`
4. В поле «Категория» выберите **Интеграция** (*Integration*) и нажмите **Добавить**.
5. Найдите появившуюся интеграцию **Soundya (Станция 2)** и нажмите **Скачать**.
6. Перезапустите Home Assistant.

---

## ⚙️ Настройка

1. В Home Assistant перейдите в **Настройки** $\to$ **Устройства и службы** $\to$ **Добавить интеграцию**.
2. В поиске введите **Soundya**.
3. Введите IP-адрес колонки (например, `192.168.1.150`) и порт `8765`.
4. Интеграция сразу подключится и создаст устройство «Станция 2».

---

## 🎛 Предоставляемые сущности и возможности

### 🎵 Медиаплеер (`media_player.station_2`)
- Воспроизведение, пауза, переключение треков, громкость, обложки треков, shuffle и repeat.
- **`play_media`**: поддержка запуска треков/плейлистов по поисковой фразе или прямой ссылке на SoundCloud в автоматизациях Home Assistant (например: `play lofi hip hop`).
- Выбор источника (`source`): `soundya`, `alice`, `airplay`, `bluetooth`, `idle`.

### 💡 88-LED матрица (`light.station_2`)
- Включение / выключение подсветки, плавная регулировка яркости.
- Установка статического цвета (RGB).
- Встроенный выбор 34 эффектов светомузыки прямо из карточки света.

### 🎨 Селекторы и регуляторы эффектов
- `select.station_2_effect`: выбор из 34 эффектов подсветки (с разделителем на спокойные и светомузыку).
- `select.station_2_palette`: выбор из 12 палитр (Северное сияние, Закат, Океан, Киберпанк и др.).
- `select.station_2_preset`: выбор сохранённого пресета подсветки.
- `number.station_2_speed`: скорость динамических эффектов подсветки.
- `number.station_2_intensity`: чувствительность матрицы к звуку.
- `number.station_2_night_brightness`: ограничение ночной яркости (при 0% матрица гаснет).

### 🔘 Сенсоры (Sensors)
- `sensor.station_2_last_heard`: **Последняя фраза, распознанная Алисой** (с таймстемпом). Позволяет запускать любые автоматизации Home Assistant по голосовым фразам, сказанным в комнате!
- `sensor.station_2_source`: Текущий источник звука (музыка soundya, Алиса, AirPlay, Bluetooth).
- `sensor.station_2_wifi_signal`: Уровень сигнала Wi-Fi (dBm и %).
- `sensor.station_2_ping`: Пинг к серверу (мс).
- `sensor.station_2_cpu_temperature`: Температура процессора колонки (°C).

### 🔌 Переключатели (Switches)
- `switch.station_2_yield`: Тумблер «Уступать Алисе» (матрица отдается родной анимации при обращении).
- `switch.station_2_night`: Тумблер ночного режима.
- `switch.station_2_equalizer`: Включение/выключение 10-полосного эквалайзера Soundya.
- `switch.station_2_share_heard`: Включение/выключение трансляции фраз Алисы в сеть.
- `switch.station_2_bypass`: Тумблер обхода блокировок (zapret).

### 🔘 Кнопки (Buttons)
- `button.station_2_like_track`: Поставить лайк текущему треку в SoundCloud.
- `button.station_2_unlike_track`: Удалить трек из понравившихся.
- `button.station_2_check_net`: Проверить сетевое соединение.

---

## 📦 Ручная установка (без HACS)

1. Скачайте архив `soundya-ha.zip` из последнего [Релиза](../../releases/latest).
2. Распакуйте папку `custom_components/soundya` в директорию `/config/custom_components/` вашего Home Assistant.
3. Перезапустите Home Assistant.
