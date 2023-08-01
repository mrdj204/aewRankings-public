from starlette.responses import RedirectResponse

from mmr_database.division import Division
from website import sql_db
from website.resources import db, Depends, html_table, load_db, return_error, Request, SessionData, TemplateResponse
from fastapi import APIRouter, Form

from website.session import get_session_info

router = APIRouter()


@router.get("/admin/test")
async def test_page(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint for testing
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    # START HERE #

    division: Division = db.get_division("M2")

    output = {
        "name": division.name,
        "abr": division.abr,
        "wrestlers": html_table(division.api_test(), id="division_table"),
    }

    results = {
        "request": request,
        "current_page": "admin",
        "session": session_data,
        "division": output,
        "hide_footer": True,
    }

    page = "wrestlers/division.html"
    # page = "admin/test.html"
    return TemplateResponse(page, results)


@router.get("/admin/debug/")
async def debug(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Debug endpoint
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    new_wrestlers = db.api_debug_new_contestants()
    for k, v in new_wrestlers.items():
        new_wrestlers[k] = sorted(v)

    output = {
        "team_errors": db.api_debug_team_errors(),
        **new_wrestlers,
        "broadcasts": db.new_broadcasts,
        "events": db.new_events,
        # "placement_points": db.api_debug_placement_points(),
    }

    results = {
        "request": request,
        "current_page": "admin",
        "session": session_data,
        "output": output,
        "hide_footer": True,
    }
    return TemplateResponse("admin/debug.html", results)


@router.get("/admin/access_logs/")
async def access_logs(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Access logs endpoint
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    sql = sql_db.SQLDatabase()
    output = sql.get_all_user_activity_html()
    sql.close()

    results = {
        "request": request,
        "current_page": "admin",
        "session": session_data,
        "output": output,
    }
    return TemplateResponse("admin/access_logs.html", results)


@router.get("/admin/access_logs/clear")
async def access_logs_clear(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to clear access logs
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    sql = sql_db.SQLDatabase()
    sql.remake_user_activity_table()
    sql.close()
    return RedirectResponse(url="/admin/access_logs")


@router.get("/admin/rankings_helper")
async def rankings_helper(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to help me create match cards
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    champions, singles, duos, trios = db.api_rankings_helper()
    champions = html_table(champions, id="champions")
    singles = '\n'.join([f'<option value="{w.name}">{w.name}</option>' for w in singles])
    duos = '\n'.join([f'<option value="{w.full_name}">{w.full_name}</option>' for w in duos])
    trios = '\n'.join([f'<option value="{w.full_name}">{w.full_name}</option>' for w in trios])

    results = {
        "request": request,
        "current_page": "admin",
        "session": session_data,
        "champions": champions,
        "singles": singles,
        "duos": duos,
        "trios": trios,
        "hide_footer": True,
    }
    return TemplateResponse("admin/rankings_helper.html", results)


@router.post("/admin/rankings_helper")
async def rankings_helper_get_wrestler(request: Request, wrestler_name: str = Form(...),
                                       session_info: dict = Depends(get_session_info)):
    """
    Endpoint to fetch wrestler/team
    """
    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    return db.api_rankings_helper_post(wrestler_name)


@router.get("/admin/matches/")
async def get_matches(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to list all matches

    TODO:
        need to rework before making available to web_users again
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    match_count = len(db.matches)
    matches = [match.to_json() for match in reversed(db.matches)]

    # Code for finding what is stretching the table
    # highest_length = 0
    # hightest_match = None
    # for match in matches:
    #     for line in match["Event"].split("<br>"):
    #         if len(line) > highest_length:
    #             highest_length = len(line)
    #             hightest_match = match
    #
    # print(hightest_match)

    matches = html_table(matches, id="match_history")
    results = {
        "request": request,
        "current_page": "matches",
        "session": session_data,
        "matches": matches,
        "match_count": match_count,
    }
    return TemplateResponse("admin/matches.html", results)


@router.get("/admin/reload")
async def reload_db(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to reload the database.

    TODO:
        broken, need to fix
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    db.initialize()

    url = request.headers["Referer"] if "Referer" in request.headers else "/"
    return RedirectResponse(url=url)


@router.get("/admin/db_debug/")
async def db_debug(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint for debugging databases
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_admin:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    sql = sql_db.SQLDatabase()
    # this clears all but the user, for keeping current rankings
    # sql.clear_rankings_submissions("HulkinBrent#6937")
    output = sql.get_all_rankings_submissions()
    sql.close()

    results = {
        "request": request,
        "current_page": "admin",
        "session": session_data,
        "output": output,
    }
    return TemplateResponse("admin/debug_db.html", results)
