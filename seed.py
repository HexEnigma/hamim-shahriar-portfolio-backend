import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from portfolio.models import Profile, Skill, Education, Experience, Project, ContactMessage
from blog.models import Category, Tag, Post, Comment

User = get_user_model()

# 1. Create the grader superuser automatically!
if not User.objects.filter(username="grader").exists():
    User.objects.create_superuser("grader", "grader@example.com", "GraderPassword123!")
    print("Created grader superuser.")
    
owner = User.objects.filter(username="grader").first()

print("Seeding database...")

# 1. Profile
Profile.objects.all().delete()
Profile.objects.create(
    full_name="Hamim Shahriar",
    headline="Full Stack Developer | Python & Django | React | REST APIs",
    bio="I'm a Computer Science and Engineering student at Northern University Bangladesh with a strong interest in full-stack web development. I enjoy building practical applications that solve real problems and make everyday tasks easier.\n\nMy current focus is Python, Django REST Framework, React, and database management. I'm always learning, improving my skills, and exploring new technologies. I also enjoy automating repetitive tasks and turning ideas into working projects.",
    github_url="https://github.com/HexEnigma",
    linkedin_url="https://www.linkedin.com/in/hamim-shahriar/", # <-- UPDATE THIS
    is_available_for_hire=True
)

# 2. Skills
skills_data = [
    ("Python", "BACKEND", 85), ("Django", "BACKEND", 80), ("Django REST Framework", "BACKEND", 75),
    ("JavaScript", "FRONTEND", 75), ("React", "FRONTEND", 70), ("HTML", "FRONTEND", 90),
    ("CSS", "FRONTEND", 80), ("Tailwind CSS", "FRONTEND", 75), ("PostgreSQL", "DATABASE", 70),
    ("MySQL", "DATABASE", 75), ("Git", "TOOLS", 80), ("GitHub", "TOOLS", 85),
    ("VS Code", "TOOLS", 90), ("C++", "BACKEND", 70)
]
for name, cat, prof in skills_data:
    Skill.objects.get_or_create(name=name, defaults={"category": cat, "proficiency": prof})

# 3. Education & Experience
Education.objects.get_or_create(
    institution="Northern University Bangladesh",
    defaults={"degree": "BSc in Computer Science & Engineering", "field_of_study": "CSE", "start_year": 2023, "end_year": 2027, "grade": "3.95"}
)
Experience.objects.get_or_create(
    company="Northern University Bangladesh",
    role="Class Representative",
    defaults={"employment_type": "PART_TIME", "start_date": "2023-01-01", "is_current": True, "description": "Coordinating class communication, sharing academic updates, and assisting with class-related activities."}
)

# 4. Projects
p1, _ = Project.objects.get_or_create(
    title="CoLab Studio",
    defaults={"summary": "Real-time collaborative platform for system design and technical documentation.", "description": "Features a visual editor, live collaboration, and workspace management.", "category": "WEB", "status": "IN_PROGRESS", "github_url": "https://github.com/HexEnigma/CoLab_Studio"}
)
p1.tech_stack.set(Skill.objects.filter(name__in=["Django", "Django REST Framework", "React", "PostgreSQL"]))

p2, _ = Project.objects.get_or_create(
    title="Habit Tracker",
    defaults={"summary": "Web application for tracking daily habits and monitoring progress.", "description": "A habit-tracking application developed as a software development and database project.", "category": "WEB", "status": "COMPLETED", "github_url": "https://github.com/HexEnigma/habit_tracker"}
)
p2.tech_stack.set(Skill.objects.filter(name__in=["MySQL", "HTML", "CSS", "JavaScript"]))

p3, _ = Project.objects.get_or_create(
    title="Budget Buddy",
    defaults={"summary": "Personal finance project for organizing expenses and managing budgets.", "description": "A full-stack application focused on personal finance.", "category": "WEB", "status": "COMPLETED", "github_url": "https://github.com/HexEnigma/Budget_Buddy"}
)
p3.tech_stack.set(Skill.objects.filter(name__in=["C"]))

# 5. Categories & Tags
c1, _ = Category.objects.get_or_create(name="Web Development")
c2, _ = Category.objects.get_or_create(name="Python & Django")
c3, _ = Category.objects.get_or_create(name="Programming & Learning")
tags = ["Python", "Django", "React", "REST API", "JavaScript", "Web Development", "PostgreSQL", "Git & GitHub"]
for t in tags:
    Tag.objects.get_or_create(name=t)

# 6. Blog Posts (Generated 300+ words)
content_1 = """Building a backend becomes more manageable when you understand how APIs connect your application to its data. This article covers serializers, views, URL routing, and the basics of building a REST API with Django.
\nWhen starting with Django REST Framework (DRF), the first concept to grasp is the Serializer. A serializer acts as a translator between complex Python objects (like Django models) and formats like JSON. It handles the heavy lifting of converting data back and forth, ensuring your frontend receives clean, structured data.
\nNext are Views. In DRF, views handle the logic of your API. You can use function-based views for simple endpoints, or class-based views (like APIView or ViewSets) for more complex operations. ViewSets are particularly powerful because they combine multiple views (list, create, retrieve, update, delete) into a single class, drastically reducing boilerplate code.
\nURL Routing is where the magic connects. By using a Router with your ViewSets, DRF automatically generates the URL patterns for your API. This means you don't have to manually map every single endpoint.
\nFinally, building a REST API is about following standard HTTP methods: GET for reading, POST for creating, PUT/PATCH for updating, and DELETE for removing. By combining serializers, views, and routers, you can build a robust API that your React frontend can easily consume."""

content_2 = """React helps developers build interactive interfaces using reusable components. Learn how components, props, and state work together to create applications that are easier to maintain and extend.
\nBefore React, developers often used direct DOM manipulation, which became messy as applications grew. React introduced a declarative approach. Instead of telling the browser *how* to change the UI step-by-step, you tell React *what* the UI should look like based on the current state.
\nComponents are the building blocks. A component is simply a JavaScript function that returns HTML-like code (JSX). You can think of them as custom, reusable HTML tags. For example, a `Button` component can be used everywhere in your app, ensuring consistent styling.
\nProps (short for properties) are how you pass data from a parent component to a child component. They are read-only, meaning a child cannot modify the data it receives. This unidirectional data flow makes debugging much easier because you always know where the data came from.
\nState is the memory of a component. When state changes, React automatically re-renders the component to reflect the new data. Hooks like `useState` allow functional components to hold and update their own state. 
\nBy combining components, props, and state, you can build complex, interactive user interfaces that are modular and easy to test."""

content_3 = """A frontend and backend need a reliable way to exchange data. This article explores how React communicates with Django REST Framework through HTTP requests, API endpoints, and JSON responses.
\nThe bridge between React and Django is the API (Application Programming Interface). When a user clicks a button in React to load their profile, React doesn't know how to talk to the database directly. Instead, it sends an HTTP request to a specific URL on your Django server.
\nAxios is a popular library used in React to make these requests. It provides a clean syntax for sending GET, POST, and other requests. For example, `axios.get('/api/profile/')` fetches the data.
\nAuthentication is a crucial part of this connection. Since Django REST Framework often uses JSON Web Tokens (JWT), React must send the token in the headers of every request to prove the user is logged in. The server checks the token, verifies the user's permissions, and if everything is valid, returns the requested data.
\nHandling asynchronous data is another challenge. The server takes time to respond, so React needs to manage loading states. Libraries like React Query make this seamless by handling caching, loading indicators, and error states automatically.
\nUnderstanding this request-response cycle is the key to building full-stack applications."""

content_4 = """Version control makes it easier to track changes, experiment safely, and collaborate with other developers. Here are the Git commands and GitHub practices I find useful when working on projects.
\nGit is a distributed version control system. Every developer has a full copy of the project history on their local machine. This means you can commit changes, create branches, and experiment without an internet connection.
\nThe most common workflow starts with `git status` to see what files have changed. Then, `git add .` stages those changes, and `git commit -m "message"` saves them to your local history.
\nWhen working on a new feature, it's best practice to create a branch: `git checkout -b feature-name`. This keeps your new code isolated from the main, stable codebase. Once the feature is complete and tested, you merge it back into the `main` branch.
\nGitHub takes Git to the next level by providing cloud hosting. `git push origin main` uploads your local commits to GitHub. This acts as a backup and allows other developers to pull your code.
\nWriting clear commit messages is a skill. Instead of "fixed stuff", write "feat: add authentication to login page". This makes the project's history easy to read and understand, which is incredibly helpful when debugging later."""

content_5 = """Developing a collaborative system design platform has taught me that building a full-stack application involves much more than writing frontend and backend code. This draft explores the challenges of real-time communication, state synchronization, and designing a maintainable application.
\n(Work in progress...)"""

posts_data = [
    ("Getting Started with Django REST Framework", "Building a backend becomes more manageable when you understand how APIs connect your application to its data.", c2, ["Python", "Django", "REST API"], "PUBLISHED", content_1),
    ("How React Makes Building User Interfaces Easier", "React helps developers build interactive interfaces using reusable components.", c1, ["React", "JavaScript", "Web Development"], "PUBLISHED", content_2),
    ("Connecting React with a Django Backend", "A frontend and backend need a reliable way to exchange data.", c1, ["React", "Django", "REST API"], "PUBLISHED", content_3),
    ("Git and GitHub: A Practical Workflow for Developers", "Version control makes it easier to track changes and collaborate with other developers.", c3, ["Git & GitHub", "Web Development"], "PUBLISHED", content_4),
    ("Building CoLab Studio: Lessons from a Full-Stack Project", "Developing a collaborative system design platform has taught me that building a full-stack application involves much more than writing code.", c1, ["Django", "React", "Web Development"], "DRAFT", content_5)
]

for title, excerpt, cat, tag_list, status, content in posts_data:
    post, _ = Post.objects.get_or_create(title=title, defaults={"excerpt": excerpt, "category": cat, "author": owner, "status": status, "content": content})
    post.tags.set(Tag.objects.filter(name__in=tag_list))

# 7. Seeding Moderation & Inbox (For Dashboard demo)
if Post.objects.filter(status="PUBLISHED").exists():
    first_post = Post.objects.filter(status="PUBLISHED").first()
    Comment.objects.get_or_create(post=first_post, name="Test Visitor", content="Great article, very helpful!", is_approved=True, email="test@example.com")
    Comment.objects.get_or_create(post=first_post, name="Spam Bot", content="Buy cheap crypto now!", is_approved=False, email="spam@example.com")
    ContactMessage.objects.get_or_create(name="Recruiter", subject="Job Opportunity", message="We loved your portfolio!", is_read=False, email="hr@techcorp.com")

print("Database successfully seeded!")