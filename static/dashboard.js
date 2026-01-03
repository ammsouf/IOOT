/**
 * Formatage du texte "il y a X secondes / minutes / heures"
 */
function formatTimeAgo(timestamp) {
  if (!timestamp) return "Horodatage non disponible";

  const now = new Date();
  const diffMs = now - timestamp;
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) {
    return `il y a ${diffSec} seconde${diffSec > 1 ? "s" : ""}`;
  }

  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) {
    return `il y a ${diffMin} minute${diffMin > 1 ? "s" : ""}`;
  }

  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) {
    return `il y a ${diffH} heure${diffH > 1 ? "s" : ""}`;
  }

  const diffD = Math.floor(diffH / 24);
  return `il y a ${diffD} jour${diffD > 1 ? "s" : ""}`;
}

/**
 * Récupère la dernière mesure depuis l’API Django /latest/
 */
async function loadLatestFromApi() {
  try {
    const response = await fetch("/latest/?t=" + Date.now());

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const temperature = data.temp;
    const humidity = data.hum;
    const tsRaw = data.dt;
    const ts = tsRaw ? new Date(tsRaw) : null;

    const tempValueEl = document.getElementById("temp-value");
    const tempTimeEl = document.getElementById("temp-time");
    const humValueEl = document.getElementById("hum-value");
    const humTimeEl = document.getElementById("hum-time");

    // Température
    if (temperature !== undefined && temperature !== null) {
      tempValueEl.textContent = `${temperature.toFixed(1)} °C`;
    } else {
      tempValueEl.textContent = "-- °C";
    }
    tempTimeEl.textContent = ts ? formatTimeAgo(ts) : "Horodatage non disponible";

    // Humidité
    if (humidity !== undefined && humidity !== null) {
      humValueEl.textContent = `${humidity.toFixed(1)} %`;
    } else {
      humValueEl.textContent = "-- %";
    }
    humTimeEl.textContent = ts ? formatTimeAgo(ts) : "Horodatage non disponible";

  } catch (error) {
    console.error("Erreur lors de l’appel à /latest/ :", error);

    const tempTimeEl = document.getElementById("temp-time");
    const humTimeEl = document.getElementById("hum-time");

    // Si une erreur survient, afficher un message générique
    if (tempTimeEl && humTimeEl) {
      tempTimeEl.textContent = "Erreur de connexion à l’API";
      humTimeEl.textContent = "Erreur de connexion à l’API";
    }
  }
}

/**
 * Initialisation : premier chargement + rafraîchissement toutes les 5 secondes
 */
document.addEventListener("DOMContentLoaded", () => {
  loadLatestFromApi();
  setInterval(loadLatestFromApi, 5000); // Rafraîchir toutes les 5 secondes
});

