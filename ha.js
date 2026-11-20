// =====================================================================
// Home Assistant Integration Mod for Soundya
// Native integration: Media Player, 88-LED Matrix, Effects, Controls
// =====================================================================
(function() {
  console.log('[Home Assistant Mod] Initializing...');

  // 1. Inject Stylesheet if not present
  if (!document.getElementById('mod-ha-css')) {
    const link = document.createElement('link');
    link.id = 'mod-ha-css';
    link.rel = 'stylesheet';
    link.href = '/mods/homeassistant/ha.css?v=' + Date.now();
    document.head.appendChild(link);
  }

  // 2. Render & Mount Home Assistant Card
  function mountHaCard() {
    if (document.getElementById('mod-ha-section')) {
      return;
    }

    const host = window.location.hostname || 'soundya.local';
    const port = window.location.port || '8765';
    const fullAddr = `http://${host}:${port}`;
    const hacsRepoUrl = 'https://github.com/Gemeur/soundya-ha';
    const hacsOneClick = `https://my.home-assistant.io/redirect/hacs_repository/?owner=Gemeur&repository=soundya-ha&category=integration`;

    const haHtml = `
      <details class="psect soundya-ha-card" id="mod-ha-section">
        <summary>Home Assistant</summary>
        <div class="ha-card-body">
          <p class="hint">
            Нативная интеграция Soundya / Lumya для Home Assistant: медиаплеер с обложками и громкостью, свет (88-LED матрица), переключатель 34 эффектов, выбор палитр, ночной режим и тумблер «Уступать Алисе». Подключается по локальной сети без брокеров MQTT.
          </p>

          <div class="ha-host-row">
            <span>Адрес колонки для подключения:</span>
            <code>${fullAddr}</code>
            <button type="button" class="btn sm" id="haCopyAddrBtn" title="Скопировать адрес">Копировать</button>
          </div>

          <div class="ha-actions">
            <a href="${hacsOneClick}" target="_blank" rel="noopener noreferrer" class="btn sm primary ha-hacs-btn">
              Добавить в Home Assistant (HACS)
            </a>
            <button type="button" class="btn sm ha-copy-btn" id="haCopyHacsBtn">
              Скопировать ссылку
            </button>
            <a href="/mods/homeassistant/soundya-ha.zip" download="soundya-ha.zip" class="btn sm ha-dl-btn" title="Скачать zip архив для ручной установки">
              Скачать ZIP
            </a>
          </div>

          <details class="guide" style="margin-top: 14px;">
            <summary>Инструкция по установке</summary>
            <ol class="hint">
              <li>Нажмите кнопку <b>«Добавить в Home Assistant (HACS)»</b> выше (или добавьте ссылку репозитория в <i>HACS → Интеграции → Пользовательские репозитории</i>).</li>
              <li>Нажмите <b>«Скачать»</b> в HACS и перезагрузите Home Assistant.</li>
              <li>Перейдите в <i>Настройки → Устройства и службы → Добавить интеграцию</i>, найдите <b>«Soundya»</b> и введите IP-адрес: <code>${host}</code>.</li>
            </ol>
          </details>

          <details class="guide" style="margin-top: 8px;">
            <summary>Сущности и управление в Home Assistant</summary>
            <div class="help-box" id="help-ha" style="margin-top: 8px;">
              <table class="help-table">
                <tbody>
                  <tr><td class="help-cmd">media_player.station_2_soundya</td><td class="help-desc">Плеер Soundya: SoundCloud, треки, обложки, громкость, поиск треков</td></tr>
                  <tr><td class="help-cmd">media_player.station_2_alisa</td><td class="help-desc">Плеер Алисы: Яндекс Музыка / радио, TTS (произношение текста), команды</td></tr>
                  <tr><td class="help-cmd">light.station_2</td><td class="help-desc">Свет: включение 88-LED матрицы, яркость, выбор статического цвета (RGB) и эффектов</td></tr>
                  <tr><td class="help-cmd">select.station_2_effect</td><td class="help-desc">Выбор из 34 эффектов (с разделением на светомузыку и плавные)</td></tr>
                  <tr><td class="help-cmd">select.station_2_palette</td><td class="help-desc">Выбор цветовой палитры матрицы (12 встроенных палитр)</td></tr>
                  <tr><td class="help-cmd">select.station_2_preset</td><td class="help-desc">Выбор сохранённого пресета подсветки</td></tr>
                  <tr><td class="help-cmd">sensor.station_2_last_heard</td><td class="help-desc">Последняя распознанная фраза Алисы (запуск автоматизаций HA по фразам голосом)</td></tr>
                  <tr><td class="help-cmd">sensor.station_2_source</td><td class="help-desc">Текущий источник звука: soundya, alice, airplay, bluetooth, idle</td></tr>
                  <tr><td class="help-cmd">sensor.station_2_wifi_signal</td><td class="help-desc">Сигнал Wi-Fi (уровень RSSI в dBm и качество связи)</td></tr>
                  <tr><td class="help-cmd">switch.station_2_equalizer</td><td class="help-desc">Включение / выключение 10-полосного эквалайзера Soundya</td></tr>
                  <tr><td class="help-cmd">switch.station_2_bypass</td><td class="help-desc">Включение / выключение обхода блокировок (zapret)</td></tr>
                  <tr><td class="help-cmd">switch.station_2_yield</td><td class="help-desc">Тумблер режима «Уступать Алисе» (панель отдается Алисе при запросах)</td></tr>
                  <tr><td class="help-cmd">switch.station_2_night</td><td class="help-desc">Тумблер ночного режима матрицы</td></tr>
                  <tr><td class="help-cmd">button.station_2_like_track</td><td class="help-desc">Кнопка «Лайк» текущего трека в SoundCloud</td></tr>
                  <tr><td class="help-cmd">number.station_2_speed</td><td class="help-desc">Регулировка скорости динамического эффекта</td></tr>
                  <tr><td class="help-cmd">number.station_2_intensity</td><td class="help-desc">Регулировка чувствительности к звуку</td></tr>
                </tbody>
              </table>
            </div>
          </details>
        </div>
      </details>
    `;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = haHtml.trim();
    const section = wrapper.firstElementChild;

    // Target mount: services subtab (preferred) or fallback to devices
    const servicesSub = document.querySelector('.sub[data-sub="services"]') || document.getElementById('sub-services');
    if (servicesSub) {
      servicesSub.appendChild(section);
    } else {
      const devicesSub = document.querySelector('.sub[data-sub="devices"]');
      if (devicesSub) {
        devicesSub.appendChild(section);
      } else {
        const settingsTab = document.getElementById('tab-settings');
        if (settingsTab) {
          settingsTab.appendChild(section);
        }
      }
    }

    // Attach event listeners
    const copyAddrBtn = document.getElementById('haCopyAddrBtn');
    if (copyAddrBtn) {
      copyAddrBtn.onclick = () => {
        copyText(fullAddr, copyAddrBtn, 'Скопировано');
      };
    }

    const copyHacsBtn = document.getElementById('haCopyHacsBtn');
    if (copyHacsBtn) {
      copyHacsBtn.onclick = () => {
        copyText(hacsRepoUrl, copyHacsBtn, 'Скопировано');
      };
    }

    function copyText(txt, btn, okText) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(() => {
          const prev = btn.textContent;
          btn.textContent = okText;
          setTimeout(() => { btn.textContent = prev; }, 2000);
        }).catch(() => {
          prompt('Скопируйте вручную:', txt);
        });
      } else {
        prompt('Скопируйте вручную:', txt);
      }
    }
  }

  // Run on DOMContentLoaded or immediately if DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountHaCard);
  } else {
    mountHaCard();
  }

  setTimeout(mountHaCard, 400);
  setTimeout(mountHaCard, 1200);
})();
