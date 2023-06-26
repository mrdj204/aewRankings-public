"""
Module: fanhub.py

This module contains API endpoints for aew fan hub.

API Endpoints:
    - /fanhub/: Root of fan hub section.
    - /fanhub/rankings/current: Retrieve and display current rankings.
    - /fanhub/rankings/current/submit: Submit rankings data.
    - /fanhub/rankings/submit: Display a form for submitting rankings.
    - /fanhub/rankings/submit/submit: Submit rankings data.
    - /fanhub/rankings/results: Retrieve and display the results of rankings submissions.
    - /fanhub/rankings/results/clear: Clear rankings submissions data.
    - /fanhub/predictions/admin: Admin section for managing predictions.

TODO:
    - fan hub predicitions
    - track power rankings history
    - spinoff seperate app
    - community rankings for events
"""

from datetime import datetime
from typing import Union

from fastapi import APIRouter
from starlette.responses import RedirectResponse

from website import sql_db
from website.resources import (db, Depends, html_table, PERMISSION_ERROR, RANKINGS_USER, Request,
                               return_error, SessionData, TemplateResponse)
from website.session import get_session_info


router = APIRouter()


@router.get("/fanhub/")
async def fanhub(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to render the fan hub base page.
    """
    session_data: SessionData = session_info["data"]
    results = {
        "request": request,
        "current_page": "fanhub",
        "session": session_data,
    }
    return TemplateResponse("fanhub/base.html", results)


@router.get("/fanhub/rankings/current")
async def fanhub_rankings(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display the current rankings.
    """
    session_data: SessionData = session_info["data"]
    results = {
        "request": request,
        "current_page": "fanhub",
        "session": session_data,
        "rankings_sub": True,
    }

    sql = sql_db.SQLDatabase()
    made_submission = sql.check_rankings_submission(RANKINGS_USER)
    if made_submission:
        submission = {k.replace("_", " "): v for k, v in sql.get_user_rankings_submission(RANKINGS_USER).items()}
        results.update({
            "sub": submission,
            "sub_html": html_table(submission),
        })
    sql.close()

    # Return view only page for non-admins
    if not session_data.fanhub_admin:
        return TemplateResponse("fanhub/power_rankings/current.html", results)

    # Get wrestler lists
    divisions: dict[str, dict[str, list[Union[str, dict[str, str]]]]] = db.api_fanhub_wrestler_list()

    results.update({
        "divisions": divisions,
        "current": True
    })
    return TemplateResponse("fanhub/power_rankings/submit.html", results)


@router.post("/fanhub/rankings/current/submit")
async def fanhub_rankings_submit(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to submit rankings data.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.fanhub_admin:
        return await return_error(request, PERMISSION_ERROR)

    form_data = await request.form()  # Access the form data from the request
    time_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    form_data = {k.replace(" ", "_").replace("'", "")[10:-1]: data for k, data in form_data.items()}

    sql = sql_db.SQLDatabase()
    condition = sql.add_rankings_submission(time_str, RANKINGS_USER, form_data)
    sql.close()
    if not condition:
        return {"error": "???"}
    return RedirectResponse(url="/fanhub/rankings/current", status_code=303)


@router.get("/fanhub/rankings/submit")
async def fanhub_submit(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to display a form for submitting rankings.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.fanhub_elite:
        return await return_error(request, PERMISSION_ERROR)

    results = {
        "request": request,
        "current_page": "fanhub",
        "session": session_data,
    }

    sql = sql_db.SQLDatabase()
    made_submission = sql.check_rankings_submission(session_data.username)
    if made_submission:
        results.update({
            "admin": True,
            "sub": {k.replace("_", " "): v for k, v in sql.get_user_rankings_submission(session_data.username).items()}
        })
    sql.close()

    divisions: dict[str, dict[str, list[Union[str, dict[str, str]]]]] = db.api_fanhub_wrestler_list()

    results.update({"divisions": divisions})
    return TemplateResponse("fanhub/power_rankings/submit.html", results)


@router.post("/fanhub/rankings/submit/submit")
async def fanhub_submit_submit(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to submit rankings data.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.fanhub_elite:
        return await return_error(request, PERMISSION_ERROR)

    form_data = await request.form()  # Access the form data from the request
    time_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    form_data = {k.replace(" ", "_").replace("'", "")[10:-1]: data for k, data in form_data.items()}

    sql = sql_db.SQLDatabase()
    condition = sql.add_rankings_submission(time_str, session_data.username, form_data)
    sql.close()
    if not condition:
        return {"error": "???"}
    return RedirectResponse(url="/fanhub/rankings/submit", status_code=303)


@router.get("/fanhub/rankings/results")
async def fanhub_results(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display the results of rankings submissions.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.fanhub_elite:
        return await return_error(request, PERMISSION_ERROR)

    sql = sql_db.SQLDatabase()
    submissions: dict[str, dict[str, str]] = {}
    total_points: dict[str, dict[str, dict[str, int]]] = {}
    who_submitted = {"submitted": []}
    # dict[title, dict[wrestler, dict[user, ranking]]]
    for user, submission in sql.get_all_rankings_submissions().items():
        user = user.replace("dan", "doomguy")
        if user not in who_submitted["submitted"] and user != "current_rankings":
            who_submitted["submitted"].append(user)
        submissions[user] = {}
        for title_rank, wrestler in submission.items():
            title_rank = title_rank.replace("_", " ")
            submissions[user][title_rank] = wrestler
            for d in db.divisions:
                w = db.get_contestant(d, wrestler)
                if w:
                    wrestler = w.name_link
                    if w.is_team and w.name:
                        wrestler += f"<br>{w.wrestlers}"
                    break
            if "Title" in title_rank:
                points = 4 - int(title_rank[-1:])
                title = title_rank[:-1].strip()
                if title not in total_points:
                    total_points[title] = {"current_rankings": {"total": -1}}
                if user == "current_rankings":
                    total_points[title]["current_rankings"].update({wrestler: points})
                else:
                    if wrestler not in total_points[title]:
                        total_points[title][wrestler] = {"total": 0}
                    total_points[title][wrestler]["total"] += points
                    total_points[title][wrestler][user] = points
    sql.close()

    # Sort the wrestlers by their "total" key for each title
    sorted_points = {}
    for title_key in total_points.keys():
        sorted_points[title_key] = {}
        title_dict = total_points[title_key]
        for wrestler_key in sorted(title_dict.keys(), key=lambda k: title_dict[k]['total'], reverse=True):
            wrestler_dict = title_dict[wrestler_key]
            sorted_points[title_key][wrestler_key] = wrestler_dict

    results = {
        "request": request,
        "current_page": "fanhub",
        "session": session_data,
        "submissions": submissions,
        "total_points": html_table(sorted_points),
        "who_submitted": html_table(who_submitted),
    }
    return TemplateResponse("fanhub/power_rankings/results.html", results)


@router.get("/fanhub/rankings/results/clear")
async def fanhub_results_clear(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to clear the rankings submissions data.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.fanhub_admin:
        return await return_error(request, PERMISSION_ERROR)

    sql = sql_db.SQLDatabase()
    sql.clear_rankings_submissions(RANKINGS_USER)
    sql.close()
    return RedirectResponse(url="/fanhub/rankings/results")


@router.get("/fanhub/predictions/admin")
async def fanhub_predictions_admin(request: Request, session_info: dict = Depends(get_session_info)):
    """
     Endpoint to render the admin section for managing predictions.
     """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.fanhub_admin:
        return await return_error(request, PERMISSION_ERROR)

    results = {
        "request": request,
        "current_page": "fanhub",
        "session": session_data,
    }
    return TemplateResponse("fanhub/predictions/admin.html", results)
