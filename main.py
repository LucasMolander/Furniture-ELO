from pathlib import Path
from typing import List, Dict, Tuple
from pprint import pprint
from math import floor, pow
from collections import defaultdict
from statistics import mean

from enum import Enum

class Winner(str, Enum):
    A = "A"
    B = "B"

class Const:
    RANKINGS_FOLDER: Path = Path(__file__).parent / "list_rankings"
    DEFAULT_ELO: float = 1000.0
    SCALE_FACTOR: float = 400.0
    # K_FACTOR: float = 32.0
    RR_ITERS: int = 100

    @staticmethod
    def getKFactor(rating: float) -> float:
        if rating <= 2100.0:
            return 32.0
        elif rating <= 2400.0:
            return 24.0
        else:
            return 16.0  # > 2400

def loadLists() -> Dict[str, List[str]]:
    files: List[Path] = [
        f
        for f in Const.RANKINGS_FOLDER.iterdir()
        if f.is_file()
    ]

    nameToStores: Dict[str, List[str]] = {}
    for f in files:
        sanName: str = f.name[0:f.name.rfind(".")]
        nameToStores[sanName] = [
            line.strip()
            for line in f.read_text().split("\n")
            if len(line.strip()) > 0
        ]
    return nameToStores

def exWinProb(ratingA: float, ratingB: float) -> float:
    return 1.0 / (1.0 + pow(10.0, (ratingB - ratingA) / Const.SCALE_FACTOR))

def newRatings(ratingA: float, ratingB: float, winner: Winner) -> Tuple[float, float]:
    winProbA: float = exWinProb(ratingA, ratingB)
    winProbB: float = 1.0 - winProbA

    scoreA: float = 1.0 if winner == Winner.A else 0.0
    scoreB: float = 1.0 if winner == Winner.B else 0.0

    # changeA: float = Const.K_FACTOR * (scoreA - winProbA)
    # changeB: float = Const.K_FACTOR * (scoreB - winProbB)

    changeA: float = Const.getKFactor(ratingA) * (scoreA - winProbA)
    changeB: float = Const.getKFactor(ratingB) * (scoreB - winProbB)

    return (ratingA + changeA, ratingB + changeB)

def roundRobin(storeToRankELO: List[Tuple[str, int, float]]) -> None:
    n = len(storeToRankELO)
    for i in range(0, n-1):
        for j in range(i+1, n):
            storeA, rankA, eloA = storeToRankELO[i]
            storeB, rankB, eloB = storeToRankELO[j]
            winner = Winner.A if rankA < rankB else Winner.B
            newEloA, newEloB = newRatings(eloA, eloB, winner)
            storeToRankELO[i] = (storeA, rankA, floor(newEloA))
            storeToRankELO[j] = (storeB, rankB, floor(newEloB))


def padSpaces(s: str, n: int) -> str:
    extraSpaces = n - len(s)
    return f"{s}{' '*extraSpaces}"

def main() -> int:
    # Preprocessing (load and set default ELO for each store)
    nameToStores: Dict[str, List[str]] = loadLists()
    nameToStoreRankELO: Dict[str, List[Tuple[str, int, float]]] = {
        name: [
            (store, i, Const.DEFAULT_ELO)
            for i, store in enumerate(stores)
        ]
        for name, stores in nameToStores.items()
    }

    # Do round robin and print results
    for name, storeRankELO in nameToStoreRankELO.items():
        for _ in range(Const.RR_ITERS):
            roundRobin(storeRankELO)

        maxStoreLen = 0
        for store, rank, elo in storeRankELO:
            maxStoreLen = max(maxStoreLen, len(store))
        nSpacesTotal = maxStoreLen + 4

        print(f"\n{name}\n{'-'*len(name)}")
        for store, rank, elo in storeRankELO:
            print(f"{padSpaces(store, nSpacesTotal)}{elo}")

    # Aggregate the ELOs together per-list of stores
    storeToELOs: Dict[str, List[float]] = defaultdict(list)
    for name, storeRankELO in nameToStoreRankELO.items():
        for store, rank, elo in storeRankELO:
            storeToELOs[store].append(elo)
    minELO: float = 1000.0
    storeToAvgelo: Dict[str, int] = {
        store: int(mean(elos))
        for store, elos in storeToELOs.items()
        if mean(elos) > minELO
    }

    # Sort by avg ELO (descending)
    storeToAvgelo = {
        k: v
        for k, v in sorted(storeToAvgelo.items(), key=lambda e: -e[1])
    }
    # Print it out
    maxStoreLen = 0
    for store in storeToAvgelo.keys():
        maxStoreLen = max(maxStoreLen, len(store))
    nSpacesTotal = maxStoreLen + 4

    printHeader: str = f"Store to avg ELO (above {minELO})"
    print(f"\n\n{printHeader}\n{'-'*len(printHeader)}")
    for store, avgElo in storeToAvgelo.items():
        print(f"{padSpaces(store, nSpacesTotal)}{avgElo}")

    return 0

if __name__ == '__main__':
    exit(main())
