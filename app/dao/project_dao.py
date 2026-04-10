from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload
from app.models.project import Project
from app import db
from typing import Optional, List

from app.models.project_emp import ProjectMember


class ProjectDAO:

    # ---------- READ ----------
    @staticmethod
    def get_by_id(id: str) -> Optional[Project]:
        """Get project by UUID with members eagerly loaded"""
        return Project.query.options(
            joinedload(Project.project_members).joinedload(ProjectMember.employee),
            joinedload(Project.project_members).joinedload(ProjectMember.role),
            joinedload(Project.bank)
        ).filter_by(id=id).first()

    @staticmethod
    def get_by_project_id(project_id: str) -> Optional[Project]:
        """Get project by project_id with members eagerly loaded"""
        return Project.query.options(
            joinedload(Project.project_members).joinedload(ProjectMember.employee),
            joinedload(Project.project_members).joinedload(ProjectMember.role),
            joinedload(Project.bank)
        ).filter_by(project_id=project_id).first()
    
    @staticmethod
    def get_all() -> List[Project]:
        """Get all projects"""
        return Project.query.all()

    @staticmethod
    def get_all_with_members() -> List[Project]:
        """Get all projects with members, roles, and bank eagerly loaded."""
        return Project.query.options(
            joinedload(Project.project_members).joinedload(ProjectMember.employee),
            joinedload(Project.project_members).joinedload(ProjectMember.role),
            joinedload(Project.bank),
        ).all()
    
    @staticmethod
    def get_all_filtered_sorted(
        page: int = 1,
        per_page: int = 10,
        bank_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """Get filtered and sorted projects with pagination"""
        query = Project.query.options(
            joinedload(Project.project_members).joinedload(ProjectMember.employee),
            joinedload(Project.project_members).joinedload(ProjectMember.role),
            joinedload(Project.bank)
        )

        # Filter by bank
        if bank_id:
            query = query.filter(Project.bank_id == bank_id)

        # Search in name, pm_name, project_id
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Project.name.ilike(search_pattern),
                    Project.pm_name.ilike(search_pattern),
                    Project.project_id.ilike(search_pattern)
                )
            )

        # Apply sorting
        sort_column = getattr(Project, sort_by, Project.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_member_by_id(member_id: str) -> Optional[ProjectMember]:
        """Get project member by member ID (UUID)"""
        return ProjectMember.query.filter_by(id=member_id).first()
    
    @staticmethod
    def get_member(project_id: str, user_id: str) -> Optional[ProjectMember]:
        """Get project member by project_id and user_id"""
        return ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
    
    @staticmethod
    def get_all_memberships_by_user(user_id: str) -> List[ProjectMember]:
        """Get all project memberships for a user (across all projects), project eagerly loaded."""
        return (
            ProjectMember.query
            .options(joinedload(ProjectMember.project))
            .filter_by(user_id=user_id)
            .all()
        )
    

    # ---------- CREATE ----------
    @staticmethod
    def create(
        name: str,
        pm_name: str,
        project_id: str,
        bank_id: Optional[str] = None,
        project_link: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Project:
        """Create new project"""
        try:
            project = Project(
                name=name,
                pm_name=pm_name,
                project_id=project_id,
                bank_id=bank_id,
                project_link=project_link,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(project)
            db.session.commit()
            return project
        except Exception:
            db.session.rollback()
            raise

    # ---------- UPDATE ----------
    @staticmethod
    def update(
        id: str,
        name: str = None,
        pm_name: str = None,
        project_id: str = None,
        bank_id: str = None,
        project_link: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> Project:
        """Update project"""
        try:
            project = ProjectDAO.get_by_id(id)
            
            if not project:
                raise ValueError("Project not found")
            
            # Validate project_id uniqueness (if changing)
            if project_id and project_id != project.project_id:
                existing = ProjectDAO.get_by_project_id(project_id)
                if existing and existing.id != project.id:
                    raise ValueError(f"Project ID '{project_id}' already exists")
            
            # Update fields
            if name is not None:
                project.name = name
            
            if pm_name is not None:
                project.pm_name = pm_name
            
            if project_id is not None:
                project.project_id = project_id
            
            if bank_id is not None:
                project.bank_id = bank_id
            
            if project_link is not None:
                project.project_link = project_link
            
            if start_date is not None:
                project.start_date = start_date
            
            if end_date is not None:
                project.end_date = end_date
            
            db.session.commit()
            return project
        except Exception:
            db.session.rollback()
            raise

    # ---------- PROJECT MEMBERS ----------
    @staticmethod
    def add_members(project_id: str, members: List[dict]) -> List[ProjectMember]:
        """Add multiple members to project
        
        Args:
            project_id: UUID of the project
            members: List of dicts with keys: user_id, allocation_percent, role_id (optional)
        
        Returns:
            List of created ProjectMember objects
        """
        try:
            created_members = []
            
            for member_data in members:
                # Check if member already exists
                existing = ProjectMember.query.filter_by(
                    project_id=project_id,
                    user_id=member_data['user_id']
                ).first()
                
                if existing:
                    # Update allocation and role if member already exists
                    existing.allocation_percent = member_data['allocation_percent']
                    if 'role_id' in member_data:
                        existing.role_id = member_data['role_id']
                    created_members.append(existing)
                else:
                    # Create new member
                    member = ProjectMember(
                        project_id=project_id,
                        user_id=member_data['user_id'],
                        allocation_percent=member_data['allocation_percent'],
                        role_id=member_data.get('role_id')
                    )
                    db.session.add(member)
                    created_members.append(member)
            
            db.session.commit()
            return created_members
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def remove_member(project_id: str, user_id: str) -> bool:
        """Remove member from project by user_id"""
        try:
            member = ProjectMember.query.filter_by(
                project_id=project_id,
                user_id=user_id
            ).first()
            
            if member:
                db.session.delete(member)
                db.session.commit()
                return True
            return False
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_member_allocation(project_id: str, user_id: str, allocation_percent: int) -> Optional[ProjectMember]:
        """Update member allocation percentage"""
        try:
            member = ProjectMember.query.filter_by(
                project_id=project_id,
                user_id=user_id
            ).first()
            
            if member:
                member.allocation_percent = allocation_percent
                db.session.commit()
                return member
            return None
        except Exception:
            db.session.rollback()
            raise