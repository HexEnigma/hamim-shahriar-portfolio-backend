"""Generate postman_collection.json:  python scripts/make_postman.py"""
import json

def cap(var, expr):
    return f'pm.collectionVariables.set("{var}", String({expr}));'

def item(name, method, path, status, auth=False, body=None, tests=(), headers=()):
    hdr = [{"key": k, "value": v} for k, v in headers]
    if auth:
        hdr.append({"key": "Authorization", "value": "Bearer {{access}}"})
    request = {"method": method, "header": hdr, "url": "{{base_url}}" + path}
    if body is not None:
        hdr.append({"key": "Content-Type", "value": "application/json"})
        request["body"] = {"mode": "raw", "raw": json.dumps(body, indent=2)}
    exec_ = [f'pm.test("{method} {path} -> {status}", function () {{ pm.response.to.have.status({status}); }});', *tests]
    return {"name": name, "request": request,
            "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": exec_}}]}

V = [("X-Visitor-Id", "{{visitor}}")]
LONG = "Postman test content for the portfolio API. " * 5   # > 100 characters

folders = {
 "1 Auth": [
  item("Login", "POST", "/auth/login/", 200, body={"username": "{{owner_username}}", "password": "{{owner_password}}"},
       tests=[cap("access", "pm.response.json().access"), cap("refresh", "pm.response.json().refresh")]),
  item("Me (owner)", "GET", "/auth/me/", 200, auth=True),
  item("Refresh token", "POST", "/auth/refresh/", 200, body={"refresh": "{{refresh}}"},
       tests=[cap("access", "pm.response.json().access"), cap("refresh", "pm.response.json().refresh")]),
 ],
 "2 Owner writes": [
  item("PATCH profile", "PATCH", "/profile/", 200, auth=True, body={"headline": "Full Stack Developer | Python & Django | React | REST APIs"}),
  item("POST skill", "POST", "/skills/", 201, auth=True, body={"name": "Postman Test Skill", "category": "TOOLS", "proficiency": 50},
       tests=[cap("skill_id", "pm.response.json().id")]),
  item("POST experience", "POST", "/experiences/", 201, auth=True,
       body={"company": "Postman Test Co", "role": "Tester", "employment_type": "FREELANCE", "start_date": "2024-01-01", "is_current": True},
       tests=[cap("exp_id", "pm.response.json().id")]),
  item("POST education", "POST", "/education/", 201, auth=True,
       body={"institution": "Postman Test Institute", "degree": "Test", "field_of_study": "QA", "start_year": 2020, "end_year": 2021},
       tests=[cap("edu_id", "pm.response.json().id")]),
  item("POST category", "POST", "/categories/", 201, auth=True, body={"name": "Postman Test Category"},
       tests=[cap("category_id", "pm.response.json().id")]),
  item("POST tag", "POST", "/tags/", 201, auth=True, body={"name": "postman-test-tag"}, tests=[cap("tag_id", "pm.response.json().id")]),
  item("POST project", "POST", "/projects/", 201, auth=True,
       body={"title": "Postman Test Project", "summary": "Created by the Postman collection.", "description": "Test project.",
             "category": "WEB", "github_url": "https://github.com/example/postman-test", "tech_stack_ids": ["{{skill_id}}"]},
       tests=[cap("project_slug", "pm.response.json().slug")]),
  item("POST post (draft)", "POST", "/posts/", 201, auth=True,
       body={"title": "Postman Test Post", "excerpt": "Created by the Postman collection.", "content": LONG,
             "category": "{{category_id}}", "tags": ["{{tag_id}}"], "status": "DRAFT"},
       tests=[cap("post_slug", "pm.response.json().slug")]),
 ],
 "3 Security (attacker view)": [
  item("Visitor cannot write a post", "POST", "/posts/", 401, body={"title": "hack"}),
  item("Register endpoint does not exist", "POST", "/auth/register/", 404),
  item("Draft is hidden from visitors", "GET", "/posts/{{post_slug}}/", 404),
  item("Draft not in public list", "GET", "/posts/", 200,
       tests=['pm.test("draft title absent", function () { pm.expect(pm.response.text()).to.not.include("Postman Test Post"); });']),
  item("Visitor cannot write a skill", "POST", "/skills/", 401, body={"name": "x"}),
  item("Visitor cannot read the inbox", "GET", "/contact/", 401),
  item("Visitor cannot read moderation list", "GET", "/comments/", 401),
  item("Visitor cannot read stats", "GET", "/dashboard/stats/", 401),
 ],
 "4 Publish and public reads": [
  item("Publish post", "PATCH", "/posts/{{post_slug}}/", 200, auth=True, body={"status": "PUBLISHED"}),
  item("GET profile", "GET", "/profile/", 200),
  item("GET skills", "GET", "/skills/?category=TOOLS", 200),
  item("GET experiences", "GET", "/experiences/", 200),
  item("GET education", "GET", "/education/", 200),
  item("GET projects", "GET", "/projects/?search=Postman", 200),
  item("GET project detail", "GET", "/projects/{{project_slug}}/", 200),
  item("GET posts", "GET", "/posts/?search=Postman&ordering=-views_count", 200),
  item("GET post detail", "GET", "/posts/{{post_slug}}/", 200, headers=V),
  item("GET categories", "GET", "/categories/", 200),
  item("GET tags", "GET", "/tags/", 200),
  item("GET owner drafts list", "GET", "/posts/?status=all", 200, auth=True),
 ],
 "5 Likes, comments, contact, moderation": [
  item("Like (on)", "POST", "/posts/{{post_slug}}/like/", 200, headers=V,
       tests=['pm.test("liked", function () { pm.expect(pm.response.json().liked).to.eql(true); });']),
  item("Like (off)", "POST", "/posts/{{post_slug}}/like/", 200, headers=V,
       tests=['pm.test("unliked", function () { pm.expect(pm.response.json().liked).to.eql(false); });']),
  item("Like without visitor header", "POST", "/posts/{{post_slug}}/like/", 400),
  item("Create comment (visitor)", "POST", "/posts/{{post_slug}}/comments/", 201,
       body={"name": "Postman Visitor", "email": "visitor@example.com", "content": "Postman test comment."}),
  item("Public comments hide unapproved", "GET", "/posts/{{post_slug}}/comments/", 200,
       tests=['pm.test("no comments yet", function () { pm.expect(pm.response.json().count).to.eql(0); });']),
  item("Moderation list (owner)", "GET", "/comments/?is_approved=false", 200, auth=True,
       tests=[cap("comment_id", "pm.response.json().results[0].id")]),
  item("Approve comment", "PATCH", "/comments/{{comment_id}}/", 200, auth=True, body={"is_approved": True}),
  item("Approved comment is public", "GET", "/posts/{{post_slug}}/comments/", 200,
       tests=['pm.test("one comment", function () { pm.expect(pm.response.json().count).to.eql(1); });',
              'pm.test("email not exposed", function () { pm.expect(pm.response.text()).to.not.include("visitor@example.com"); });']),
  item("Create contact message (visitor)", "POST", "/contact/", 201,
       body={"name": "Postman Visitor", "email": "visitor@example.com", "subject": "Postman test", "message": "Hello from the Postman collection."}),
  item("Contact inbox (owner)", "GET", "/contact/?is_read=false", 200, auth=True, tests=[cap("message_id", "pm.response.json().results[0].id")]),
  item("Mark message read", "PATCH", "/contact/{{message_id}}/", 200, auth=True, body={"is_read": True}),
  item("Dashboard stats", "GET", "/dashboard/stats/", 200, auth=True),
 ],
 "6 Cleanup": [
  item("DELETE post", "DELETE", "/posts/{{post_slug}}/", 204, auth=True),
  item("DELETE project", "DELETE", "/projects/{{project_slug}}/", 204, auth=True),
  item("DELETE category", "DELETE", "/categories/{{category_id}}/", 204, auth=True),
  item("DELETE tag", "DELETE", "/tags/{{tag_id}}/", 204, auth=True),
  item("DELETE skill", "DELETE", "/skills/{{skill_id}}/", 204, auth=True),
  item("DELETE experience", "DELETE", "/experiences/{{exp_id}}/", 204, auth=True),
  item("DELETE education", "DELETE", "/education/{{edu_id}}/", 204, auth=True),
  item("DELETE contact message", "DELETE", "/contact/{{message_id}}/", 204, auth=True),
 ],
 "7 Logout": [
  item("Logout (blacklist refresh)", "POST", "/auth/logout/", 200, auth=True, body={"refresh": "{{refresh}}"}),
 ],
}

collection = {
    "info": {"name": "DevFolio API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
             "description": "Run top to bottom with the Collection Runner. Set owner_username/owner_password first."},
    "variable": [
        {"key": "base_url", "value": "http://127.0.0.1:8000/api"},
        {"key": "owner_username", "value": "CHANGE_ME"},
        {"key": "owner_password", "value": "CHANGE_ME"},
        {"key": "visitor", "value": "postman-visitor-1"},
    ],
    "item": [{"name": n, "item": items} for n, items in folders.items()],
}

with open("postman_collection.json", "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=2)
print("Wrote postman_collection.json")