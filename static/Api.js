async function sendData() {
  const temperature = parseFloat(document.getElementById("temperatureInput").value);
  const humedite = parseFloat(document.getElementById("humediteInput").value);

  // Vérifier que les deux champs sont remplis
  if (isNaN(temperature) || isNaN(humedite)) {
    alert("Veuillez entrer à la fois la température et l'humidité avec des valeurs valides.");
    return;
  }

  console.log("Température:", temperature, "Humidité:", humedite);

  // Désactiver les champs et le bouton pour éviter plusieurs soumissions
  document.getElementById("temperatureInput").disabled = true;
  document.getElementById("humediteInput").disabled = true;
  document.querySelector("#card-Test button").disabled = true;

  try {
    // Envoi de la requête POST à l'API
    const response = await fetch("/api/endpoint/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        temperature: temperature,
        humedite: humedite
      }),
    });

    if (response.ok) {
      const responseData = await response.json();
      console.log("Réponse de l'API:", responseData);

      // Mise à jour des cartes de température et d'humidité sur le tableau de bord
      document.getElementById("temp-value").textContent = `${temperature} °C`;
      document.getElementById("hum-value").textContent = `${humedite} %`;

      // Affichage du message de succès
      alert("✅ Les données ont été envoyées avec succès!");

      // Recharger la page pour voir l'incident mis à jour (si créé/fermé)
      setTimeout(() => {
        window.location.reload();
      }, 1000);

    } else {
      // Si la réponse est une erreur, afficher les détails de l'erreur
      const errorData = await response.json();
      console.error("Erreur API:", errorData);
      alert(`❌ Erreur lors de l'envoi des données : ${errorData.error || "Erreur inconnue"}\nCode HTTP: ${response.status}`);
    }
  } catch (error) {
    console.error("Erreur de requête:", error);
    alert("❌ Une erreur s'est produite lors de la requête.");
  } finally {
    // Réactiver les champs et le bouton après la requête
    document.getElementById("temperatureInput").disabled = false;
    document.getElementById("humediteInput").disabled = false;
    document.querySelector("#card-Test button").disabled = false;
  }
}

// Fonction pour soumettre un commentaire
async function submitComment(incidentId) {
    const comment = document.getElementById('operator_1_comment').value;

    // Vérifier que le commentaire n'est pas vide
    if (!comment.trim()) {
        alert("⚠️ Veuillez entrer un commentaire avant de soumettre.");
        return;
    }

    try {
        const response = await fetch('/submit_comment/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                incident_id: incidentId,
                comment: comment
            }),
        });

        if (response.ok) {
            const responseData = await response.json();
            alert("✅ " + responseData.message);
        } else {
            console.error("Erreur lors de la soumission du commentaire");
            alert("❌ Erreur lors de la soumission du commentaire.");
        }
    } catch (error) {
        console.error('Erreur de réseau ou autre:', error);
        alert("❌ Une erreur s'est produite lors de la soumission du commentaire.");
    }
}