#!/usr/bin/env python3
"""
Script to generate ticket data for a project using the API.
Usage: python generate_tickets.py <project_id> [num_tickets]

This script uses the Flask API to create tickets, so it works
without direct database access.
"""

import sys
import requests
import random
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000/api"
EMAIL = "brian.nguyen@techvify.com.vn"
PASSWORD = "123456"


def login():
    """Login and get auth token"""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return None
    
    data = response.json()
    return data["user"]["access_token"]


def get_projects(token):
    """Get list of projects"""
    response = requests.get(
        f"{API_BASE_URL}/projects",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"❌ Failed to get projects: {response.text}")
        return None
    
    return response.json()["data"]


def get_ticket_types(token):
    """Get list of ticket types"""
    response = requests.get(
        f"{API_BASE_URL}/ticket-types",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"❌ Failed to get ticket types: {response.text}")
        return None
    
    return response.json()["data"]


def get_ticket_statuses(token):
    """Get list of ticket statuses"""
    response = requests.get(
        f"{API_BASE_URL}/ticket-statuses",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"❌ Failed to get ticket statuses: {response.text}")
        return None
    
    return response.json()["data"]


def get_employees(token):
    """Get list of employees"""
    response = requests.get(
        f"{API_BASE_URL}/employees",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"❌ Failed to get employees: {response.text}")
        return None
    
    return response.json()["data"]


def create_ticket(token, project_id, ticket_data):
    """Create a ticket"""
    response = requests.post(
        f"{API_BASE_URL}/tickets",
        json=ticket_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def get_roles(token):
    """Get list of roles"""
    response = requests.get(
        f"{API_BASE_URL}/roles",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"❌ Failed to get roles: {response.text}")
        return None
    
    return response.json()["data"]

def list_projects():
    """List all available projects"""
    token = login()
    if not token:
        return
    
    projects = get_projects(token)
    if not projects:
        print("No projects found.")
        return
    
    print("\n📋 Available Projects:")
    print("-" * 80)
    for p in projects:
        print(f"ID: {p['id']}")
        print(f"  Name: {p['name']}")
        print(f"  Project ID: {p['projectId']}")
        print(f"  PM: {p['pmName']}")
        print("-" * 80)


def generate_tickets(project_id: str, num_tickets: int = 10):
    """Generate ticket data for a specific project"""
    # Login
    print("🔐 Logging in...")
    token = login()
    if not token:
        return
    
    print("✅ Logged in successfully!")
    
    # Get project info
    projects = get_projects(token)
    project = next((p for p in projects if p["id"] == project_id), None)
    if not project:
        print(f"❌ Project with ID '{project_id}' not found!")
        print("\nAvailable projects:")
        for p in projects:
            print(f"  - {p['id']}: {p['name']}")
        return
    
    print(f"\n📌 Generating tickets for project: {project['name']} ({project['projectId']})")
    
    # Get related data
    ticket_types = get_ticket_types(token)
    ticket_statuses = get_ticket_statuses(token)
    employees = get_employees(token)
    roles = get_roles(token)
    print(f" role: {roles}")
    
    print(f"  - Employees available: {len(employees)}")
    print(f"  - Ticket types available: {len(ticket_types)}")
    print(f"  - Ticket statuses available: {len(ticket_statuses)}")
    print(f"  - Roles available: {len(roles)}")
    
    # Generate tickets
    created_tickets = []
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    for i in range(num_tickets):
        # Generate ticket_id
        ticket_id = f"TICKET-{project['projectId'][:4].upper()}-{current_year}{current_month:02d}{i+1:04d}"
        
        # Random assignments
        employee = random.choice(employees) if employees else None
        ticket_type = random.choice(ticket_types) if ticket_types else None
        ticket_status = random.choice(ticket_statuses) if ticket_statuses else None
        
        # Generate week and month (validate against current month)
        # Get the number of weeks in the current month using the API
        weeks_response = requests.post(
            f"{API_BASE_URL}/tickets/weeks",
            json={"month": current_month},
            headers={"Authorization": f"Bearer {token}"}
        )
        if weeks_response.status_code == 200:
            valid_weeks = weeks_response.json().get("data", {}).get("weeks", [])
            max_weeks = len(valid_weeks)
        else:
            max_weeks = 5  # Default fallback
        
        week = random.randint(1, max_weeks)
        
        # Create ticket data (week should be a string like "1" or "1 (01/02/2026-07/02/2026)")
        # Only include fields with valid values (not None)
        ticket_data = {
            "ticketId": ticket_id,
            "projectId": project_id,
            "week": str(week),  # Pass as string for the API
            "month": current_month
        }
        
        # Add optional fields only if they have values
        if random.random() > 0.3:
            ticket_data["ticketLink"] = f"https://jira.example.com/browse/{ticket_id}"
        
        if employee and employee.get("id"):
            ticket_data["employeeId"] = employee["id"]
        
        if ticket_type and ticket_type.get("id"):
            ticket_data["ticketTypeId"] = ticket_type["id"]
        
        if ticket_status and ticket_status.get("id"):
            ticket_data["ticketStatusId"] = ticket_status["id"]
            
        if roles and len(roles) > 0:
            # Select random roles (can be multiple)
            num_roles = random.randint(0, min(3, len(roles)))  # Up to 3 roles
            selected_roles = random.sample(roles, num_roles)
            role_ids = [role.get("roleUuid") for role in selected_roles if role.get("roleUuid")]
            if role_ids:
                ticket_data["roleIds"] = role_ids
        
        # Create ticket via API
        response = create_ticket(token, project_id, ticket_data)
        
        if response.status_code in [200, 201]:
            created_tickets.append(ticket_id)
            print(f"  ✅ Created: {ticket_id}")
        else:
            try:
                error = response.json()
                message = error.get("message", "Unknown error")
                # Show validation errors if any
                if error.get("errors"):
                    message = f"{message} - {error.get('errors')}"
            except:
                message = response.text[:100]
            print(f"  ⚠️  Failed: {ticket_id} - {message}")
    
    print(f"\n✅ Successfully created {len(created_tickets)} tickets!")
    if created_tickets:
        print("\n📝 Created tickets:")
        for tid in created_tickets:
            print(f"  - {tid}")


def main():
    print("=" * 80)
    print("🎫 Ticket Generator Script (API Version)")
    print("=" * 80)
    
    if len(sys.argv) < 2:
        # No project_id provided, list projects
        list_projects()
        print("\n📖 Usage:")
        print("  python generate_tickets.py <project_id> [num_tickets]")
        print("\nExample:")
        print("  python generate_tickets.py f7652515-5ef9-457f-9b19-08e6752957f8 20")
        sys.exit(1)
    
    project_id = sys.argv[1]
    
    # Optional: number of tickets to generate (default: 10)
    num_tickets = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    generate_tickets(project_id, num_tickets)


if __name__ == "__main__":
    main()

