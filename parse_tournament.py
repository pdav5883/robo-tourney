"""
tournament: list of rounds (don't include first four)
round: list of games in the round (all regions)
game: ((rankA, teamA, scoreA), (rankB, teamB, scoreB), winner, location)
winner: 0 if teamA wins, 1 if teamB wins
"""


import sys
from bs4 import BeautifulSoup
import requests


base_url = "https://www.sports-reference.com/cbb/postseason/YYYY-ncaa.html"


def parse_tournament(tournament_year):
    tournament_url = base_url.replace("YYYY", str(tournament_year))

    req = requests.get(tournament_url)
    tournament = BeautifulSoup(req.content, "html.parser")
    brackets = tournament.find("div", {"id": "brackets"}).find_all("div", recursive=False)

    # order of region reflects config of regions in bracket
    region1_bs4 = brackets[0].find("div", {"id":"bracket", "class":"team16"}).find_all("div", {"class":"round"})
    region2_bs4 = brackets[1].find("div", {"id":"bracket", "class":"team16"}).find_all("div", {"class":"round"})
    region3_bs4 = brackets[2].find("div", {"id":"bracket", "class":"team16"}).find_all("div", {"class":"round"})
    region4_bs4 = brackets[3].find("div", {"id":"bracket", "class":"team16"}).find_all("div", {"class":"round"})
    final4_bs4 = brackets[4].find("div", {"id":"bracket", "class":"team4"}).find_all("div", {"class":"round"})
    
    region1 = parse_region(region1_bs4)
    region2 = parse_region(region2_bs4)
    region3 = parse_region(region3_bs4)
    region4 = parse_region(region4_bs4)
    final4 = parse_final4(final4_bs4)

    regions = reorder_regions([region1, region2, region3, region4], final4)
    
    rounds = []
    
    for reg1, reg2, reg3, reg4 in zip(regions[0], regions[1], regions[2], regions[3]):
        r = []
        r.extend(reg1)
        r.extend(reg2)
        r.extend(reg3)
        r.extend(reg4)
        rounds.append(r)
        
    rounds.extend(final4)
        
    return rounds


def parse_region(region_bs4):
    round64, round32, round16, round8 = region_bs4[0], region_bs4[1], region_bs4[2], region_bs4[3]
    
    return [parse_round(round64),
            parse_round(round32),
            parse_round(round16),
            parse_round(round8)]


def parse_final4(final4_bs4):
    round4, round2 = final4_bs4[0], final4_bs4[1]
    
    return [parse_round(round4),
            parse_round(round2)]


def parse_round(round_bs4):
    # round is within a single region, or final 4
    games = []
    for game in round_bs4.findChildren("div", recursive=False):
        games.append(parse_game(game))        
    
    return games


def parse_game(game_bs4):
    teams = game_bs4.findChildren("div", recursive=False)
    teamA = parse_team(teams[0])
    teamB = parse_team(teams[1])
    
    if teamA[2] > teamB[2]:
        winner = 0
    elif teamA[2] < teamB[2]:
        winner = 1
    else:
        winner = None
    
    # format will change if game is not played
    try:
        loc = game_bs4.findChildren("span", recursive=False)[0].find("a").text[3:]
    except AttributeError:
        loc = game_bs4.findChildren("span", recursive=False)[0].text[3:]
    
    return teamA, teamB, winner, loc
    
    
def parse_team(team_bs4):
    team = []
    for line in team_bs4.children:
        if line.name:
            team.append(line.text)
            
    # if game is cancelled (VCU vs. Oregon 2021) then there won't be a score
    try:        
        return int(team[0]), team[1], int(team[2])
    except IndexError:
        return int(team[0]), team[1], 0


def reorder_regions(regions, final4):
    # reorder regions based on final 4 ordering
    regions_dict = {r[-1][0][r[-1][0][2]][1]:r for r in regions}
    team1, team2, team3, team4  = final4[0][0][0][1], final4[0][0][1][1], final4[0][1][0][1], final4[0][1][1][1]

    return [regions_dict[team1], regions_dict[team2], regions_dict[team3], regions_dict[team4]]


if __name__ == "__main__":
    rounds = parse_tournament(sys.argv[1])

    for r in rounds:
        print("\n=================================")
        print("Round of", len(r) * 2)
        print("=================================")

        for g in r:
            if g[2] is not None:
                winner = g[g[2]][1]
            else:
                winner = "NO CONTEST"

            print(g, "-->", winner)

