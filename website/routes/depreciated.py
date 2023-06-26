@app.get("/matchups/")
async def matchups(request: Request, session_info: dict = Depends(get_session_info)):
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    divisions = {}
    for division in db.divisions:
        divisions.update({division.abr: division.abr})
    results = {
        "request": request,
        "current_page": "matchups",
        "session": session_data,
        "divisions": divisions,
    }
    return TemplateResponse("matchups.html", results)


@app.get("/matchups/division/{division}/")
async def matchups_get_wrestlers(request: Request, division: str, session_info: dict = Depends(get_session_info)):
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    division = db.get_division(division)
    wrestlers = ["Select"]
    if division.duos:
        for wrestler in division.api_list_wrestlers("full_name"):
            wrestlers.append(wrestler["full_name"])
    else:
        for wrestler in division.api_list_wrestlers("name"):
            wrestlers.append(wrestler["name"])
    return {"wrestlers": wrestlers}


@app.get("/matchups/{division}/{name1}/{name2}/{name3}/{name4}/")
async def matchups_get_wrestlers_stats(request: Request, division: str, name1: str, name2: str, name3: str, name4: str,
                                       session_info: dict = Depends(get_session_info)):
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    division = db.get_division(division)
    names = [name1, name2, name3, name4]
    names = [name for name in names if name != 'Select']

    wrestlers = [db.get_contestant(division, name) for name in names]
    if len(wrestlers) == 2:
        win1 = f"{round(util_mmrDB.Probability(wrestlers[1].mmr_dict['mmr'], wrestlers[0].mmr_dict['mmr']) * 100)}%"
        win2 = f"{round(util_mmrDB.Probability(wrestlers[0].mmr_dict['mmr'], wrestlers[1].mmr_dict['mmr']) * 100)}%"
        win_chance = [win1, win2]
        vs_record = wrestlers[0].record_vs(wrestlers[1])
        vs_record = [f"{x} win(s)" for x in vs_record]
    else:
        win_chance = ["N/A" for _ in wrestlers]
        vs_record = ["N/A" for _ in wrestlers]

    stat = {
        "name": [str(wrestler) for wrestler in wrestlers],
        "mmr": [round(wrestler.mmr_dict['mmr']) for wrestler in wrestlers],
        "win_chance": win_chance,
        "record": ["-".join(str(record) for record in wrestler.yearly_record) for wrestler in wrestlers],
        "record_alltime": ["-".join(str(record) for record in wrestler.record) for wrestler in wrestlers],
        "streak": [" ".join(str(value) for value in wrestler.streak.values()) for wrestler in wrestlers],
        "vs_record": vs_record,
    }

    table = "<table border=1 style='margin-top: 10px; margin-bottom: 10px'>"
    for key, elements in stat.items():
        table += f"<tr><th>{key}</th>"
        for element in elements:
            table += f"<td>{element}</td>"
        table += f"</tr>"

    table += "</table>"
    return {"wrestlers": table}


@app.get("/generate_screenshot")
async def take_screenshot(request: Request):
    # Get the server's base URL dynamically
    base_url = str(request.base_url)

    # Construct the relative route
    relative_route = "/rankings"

    # Construct the complete URL to load
    url = base_url + relative_route

    # Configure Selenium WebDriver
    driver_service = Service("chromedriver.exe")  # Replace with the actual path to your chromedriver executable
    driver = webdriver.Chrome(service=driver_service)

    # Load the URL in the WebDriver
    driver.get("http://10.0.30.1/rankings")

    # Take a screenshot
    screenshot_path = "screenshot.png"  # Replace with the desired path to save the screenshot
    driver.save_screenshot(screenshot_path)

    # Close the WebDriver
    driver.quit()

    # Send the screenshot as a download
    return FileResponse(screenshot_path, filename="screenshot.png")


@router.get("/w/{current_wrestler}/{new_wrestler}/")
async def get_wrestler_matchup(request: Request, current_wrestler: str, new_wrestler: str,
                               session_info: dict = Depends(get_session_info)):
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    # Get wrestlers from names
    contestant1, contestant2, division = None, None, None

    for d in db.divisions:
        contestant1 = db.get_contestant(d, current_wrestler)
        contestant2 = db.get_contestant(d, new_wrestler)
        if contestant1 and contestant2:
            break
    else:
        if type(contestant1) != type(contestant2):
            error = f"{current_wrestler} is {contestant1 if contestant1 else 'lol'}"
            error += f"<br>{new_wrestler} is {contestant2 if contestant2 else 'lol'}"
            return {"error": error}
        if not contestant1 or not contestant2:
            return {"error2": f"{current_wrestler} is {type(contestant1)}\n{new_wrestler} is {type(contestant2)}"}

    # Get names
    c1_name = contestant1.name if contestant1.name else contestant1.wrestlers
    c2_name = contestant2.name if contestant2.name else contestant2.wrestlers

    # Get matches between wrestlers
    matches_vs_raw = contestant1.matches_vs(contestant2)
    matches_vs_raw_opposite = contestant2.matches_vs(contestant1)
    matches_vs = []
    for match, match_opposite in zip(reversed(matches_vs_raw), reversed(matches_vs_raw_opposite)):
        if match['points'] != "-":
            w1_won = int(match["points"]['mmr']) > 0
            w2_won = int(match["points"]['mmr']) < 0
        else:
            w1_won, w2_won = None, None
        if w1_won:
            if match['mmr'] == "-":
                winner = f"{c1_name} ({round(float(match_opposite['opponent_mmr']))})"
            else:
                winner = f"{c1_name} ({round(float(match['mmr']['mmr']))})"
            loser = f"{c2_name} ({match['opponent_mmr']['mmr']})"
        elif w2_won:
            winner = f"{c2_name} ({match['opponent_mmr']['mmr']})"
            loser = f"{c1_name} ({round(match['mmr']['mmr'] - match['points']['mmr'])})"
        else:  # draw
            winner, loser = "DRAW", "DRAW"

        element = {
            "date": match["date"],
            "event": match["event"],
            "title": match["title"] if match["title"] else "",
            "match_type": match["match_type"],
            "winner": winner,
            "plus_minus": f"± {match['points']['mmr']}" if match['points'] != "-" else "-",
            "loser": loser,
        }
        matches_vs.append(element)

    # Get win probabilities
    w1_win_chance = 100 * (1 - util_mmrDB.Probability(contestant1.mmr_dict['mmr'], contestant2.mmr_dict['mmr']))
    w2_win_chance = 100 * (1 - util_mmrDB.Probability(contestant2.mmr_dict['mmr'], contestant1.mmr_dict['mmr']))

    # Create dictionary
    results = {
        "request": request,
        "current_page": "wrestlers",
        "wrestler1": contestant1,
        "wrestler2": contestant2,
        "w1mmr": round(contestant1.mmr_dict['mmr']),
        "w2mmr": round(contestant2.mmr_dict['mmr']),
        "w1titles": contestant1.api_titles(current=1, previous=1),
        "w2titles": contestant2.api_titles(current=1, previous=1),
        "w1record": f"{contestant1.record[0]} - {contestant1.record[1]} - {contestant1.record[2]}",
        "w2record": f"{contestant2.record[0]} - {contestant2.record[1]} - {contestant2.record[2]}",
        "w1_win_chance": f"{round(w1_win_chance)}%",
        "w2_win_chance": f"{round(w2_win_chance)}%",
        "record_vs": contestant1.record_vs(contestant2),
        "matches_vs": matches_vs,
        "current_year": db.current_year,
        "w1_current_record": f"{' - '.join(contestant1.yearly_record)}",
        "w2_current_record": f"{' - '.join(contestant2.yearly_record)}",
        "w1_rank": contestant1.rank_dict[contestant1.main_mmr_keys[0]]["rank"],
        "w2_rank": contestant2.rank_dict[contestant2.main_mmr_keys[0]]["rank"],
    }
    return TemplateResponse("wrestlers/wrestler_matchup.html", results)
