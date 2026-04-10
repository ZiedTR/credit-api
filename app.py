from flask import Flask, request, jsonify
import math

app = Flask(__name__)

def calculer_mensualite(montant, taux_mensuel, duree):
    if taux_mensuel == 0:
        return montant / duree
    return montant * (taux_mensuel * (1 + taux_mensuel)**duree) / ((1 + taux_mensuel)**duree - 1)

def calculer_tableau(montant, taux_mensuel, duree, mensualite):
    tableau = []
    capital_restant = montant
    for mois in range(1, duree + 1):
        interet = capital_restant * taux_mensuel
        capital = mensualite - interet
        capital_restant -= capital
        tableau.append({
            "mois": mois,
            "mensualite": round(mensualite, 2),
            "capital": round(capital, 2),
            "interet": round(interet, 2),
            "capital_restant": round(max(capital_restant, 0), 2)
        })
    return tableau

@app.route('/simuler', methods=['GET'])
def simuler_credit():
    # Paramètres de base
    montant = float(request.args.get('montant', 0))
    taux = float(request.args.get('taux', 0))
    duree = int(request.args.get('duree', 0))
    apport = float(request.args.get('apport', 0))
    
    # Frais
    frais_dossier = float(request.args.get('frais_dossier', 0))
    frais_garantie = float(request.args.get('frais_garantie', 0))
    taux_assurance = float(request.args.get('taux_assurance', 0))
    
    # Revenus pour capacité d'emprunt
    revenus = float(request.args.get('revenus', 0))
    charges = float(request.args.get('charges', 0))

    if montant <= 0 or taux <= 0 or duree <= 0:
        return jsonify({"erreur": "Paramètres invalides"}), 400

    montant_finance = montant - apport
    taux_mensuel = (taux / 100) / 12
    mensualite = calculer_mensualite(montant_finance, taux_mensuel, duree)
    
    # Assurance mensuelle
    assurance_mensuelle = (montant_finance * (taux_assurance / 100)) / 12
    mensualite_totale = mensualite + assurance_mensuelle
    
    # Coûts totaux
    cout_total = mensualite_totale * duree
    cout_credit = cout_total - montant_finance
    cout_assurance = assurance_mensuelle * duree
    cout_frais = frais_dossier + frais_garantie
    
    # TAEG
    cout_total_taeg = cout_credit + cout_assurance + cout_frais
    taeg = ((cout_total_taeg / montant_finance) / (duree / 12)) * 100

    # Tableau amortissement
    tableau = calculer_tableau(montant_finance, taux_mensuel, duree, mensualite)
    
    # Capacité d'emprunt
    capacite = {}
    if revenus > 0:
        taux_endettement = ((mensualite_totale + charges) / revenus) * 100
        mensualite_max = (revenus * 0.35) - charges
        montant_max = mensualite_max * ((1 - (1 + taux_mensuel)**-duree) / taux_mensuel)
        capacite = {
            "taux_endettement": round(taux_endettement, 2),
            "mensualite_max_possible": round(mensualite_max, 2),
            "montant_max_empruntable": round(montant_max, 2),
            "eligible": taux_endettement <= 35
        }

    # Remboursement anticipé
    mois_anticipe = int(request.args.get('mois_anticipe', 0))
    remboursement_anticipe = {}
    if mois_anticipe > 0 and mois_anticipe < duree:
        capital_restant_anticipe = tableau[mois_anticipe - 1]['capital_restant']
        penalite_legale = min(capital_restant_anticipe * 0.03, 6 * mensualite * (taux / 100) / 12)
        remboursement_anticipe = {
            "capital_restant": round(capital_restant_anticipe, 2),
            "penalite_max_legale": round(penalite_legale, 2),
            "total_a_payer": round(capital_restant_anticipe + penalite_legale, 2)
        }

    return jsonify({
        "simulation": {
            "montant_emprunte": round(montant_finance, 2),
            "apport": apport,
            "duree_mois": duree,
            "duree_annees": round(duree / 12, 1),
            "taux_nominal": taux,
            "taeg": round(taeg, 3)
        },
        "mensualites": {
            "hors_assurance": round(mensualite, 2),
            "assurance": round(assurance_mensuelle, 2),
            "totale": round(mensualite_totale, 2)
        },
        "couts": {
            "cout_credit": round(cout_credit, 2),
            "cout_assurance": round(cout_assurance, 2),
            "frais_dossier": frais_dossier,
            "frais_garantie": frais_garantie,
            "cout_total": round(cout_total + cout_frais, 2)
        },
        "capacite_emprunt": capacite,
        "remboursement_anticipe": remboursement_anticipe,
        "tableau_amortissement": tableau
    })

@app.route('/comparer', methods=['GET'])
def comparer_offres():
    montant = float(request.args.get('montant', 0))
    duree = int(request.args.get('duree', 0))
    
    taux1 = float(request.args.get('taux1', 0))
    taux2 = float(request.args.get('taux2', 0))
    taux3 = float(request.args.get('taux3', 0))

    offres = []
    for i, taux in enumerate([taux1, taux2, taux3], 1):
        if taux > 0:
            taux_mensuel = (taux / 100) / 12
            mensualite = calculer_mensualite(montant, taux_mensuel, duree)
            cout_total = mensualite * duree
            offres.append({
                "offre": i,
                "taux": taux,
                "mensualite": round(mensualite, 2),
                "cout_total": round(cout_total, 2),
                "cout_credit": round(cout_total - montant, 2)
            })
    
    if offres:
        meilleure = min(offres, key=lambda x: x['cout_total'])
        meilleure['recommandee'] = True

    return jsonify({
        "montant": montant,
        "duree_mois": duree,
        "offres": offres
    })

@app.route('/capacite', methods=['GET'])
def capacite_emprunt():
    revenus = float(request.args.get('revenus', 0))
    charges = float(request.args.get('charges', 0))
    taux = float(request.args.get('taux', 0))
    duree = int(request.args.get('duree', 0))

    if revenus <= 0 or taux <= 0 or duree <= 0:
        return jsonify({"erreur": "Paramètres invalides"}), 400

    taux_mensuel = (taux / 100) / 12
    mensualite_max = (revenus * 0.35) - charges
    montant_max = mensualite_max * ((1 - (1 + taux_mensuel)**-duree) / taux_mensuel)

    return jsonify({
        "revenus_mensuels": revenus,
        "charges_mensuelles": charges,
        "mensualite_max": round(mensualite_max, 2),
        "montant_max_empruntable": round(montant_max, 2),
        "taux_endettement_max": 35,
        "taux": taux,
        "duree_mois": duree
    })

if __name__ == '__main__':
    app.run(debug=True, port=5002)
