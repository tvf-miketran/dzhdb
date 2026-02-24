from typing import Optional, List, Dict, Any, Tuple
from app.dao.employee_dao import EmployeeDAO
from app.dao.project_dao import ProjectDAO
from app.models.project import Project


class ProjectService:
    
    @staticmethod
    def get_all() -> List[Project]:
        """Get all projects"""
        return ProjectDAO.get_all()
    
    @staticmethod
    def get_all_filtered_sorted(
        page: int = 1,
        per_page: int = 10,
        bank_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get filtered and sorted projects with pagination"""
        
        # Validate sort_by field
        valid_sort_fields = ["created_at", "name", "pm_name", "project_id"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"
        
        pagination = ProjectDAO.get_all_filtered_sorted(
            page=page,
            per_page=per_page,
            bank_id=bank_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            "items": [ProjectService._to_dict(project) for project in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
            "filters": {
                "bank_id": bank_id,
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    
    @staticmethod
    def get_by_id(id: str) -> Optional[Project]:
        """Get project by UUID"""
        return ProjectDAO.get_by_id(id)
    
    @staticmethod
    def get_by_project_id(project_id: str) -> Optional[Project]:
        """Get project by project_id"""
        return ProjectDAO.get_by_project_id(project_id)
    
    @staticmethod
    def _to_dict(project: Project, include_members: bool = False) -> Dict[str, Any]:
        """Convert project to dictionary"""
        result = {
            "id": str(project.id),
            "projectId": project.project_id,
            "name": project.name,
            "pmName": project.pm_name,
            "projectLink": project.project_link,
            "bankId": str(project.bank_id) if project.bank_id else None,
            "bankName": project.bank.name if project.bank else None,
            "createdAt": project.created_at.isoformat() if project.created_at else None,
            "startDate": project.start_date.isoformat() if project.start_date else None,
            "endDate": project.end_date.isoformat() if project.end_date else None
        }
        
        # Add members information if requested
        if include_members:
            result["members"] = [
                {
                    "id": str(member.id),
                    "userId": str(member.user_id),
                    "employeeId": member.employee.employeeId if member.employee else None,
                    "vnFullName": member.employee.vn_full_name if member.employee else None,
                    "enFullName": member.employee.en_full_name if member.employee else None,
                    "email": member.employee.email if member.employee else None,
                    "allocationPercent": member.allocation_percent,
                    "joinedAt": member.joined_at.isoformat() if member.joined_at else None
                }
                for member in project.project_members
            ]
            result["memberCount"] = len(project.project_members)
        
        return result
        
    @staticmethod
    def create(
        name: str,
        pm_name: str,
        project_id: str,
        bank_id: Optional[str] = None,
        project_link: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[Optional[Project], Optional[List[str]]]:
        """Create new project with validation"""
        errors = []
        
        # Check if project_id already exists
        if ProjectDAO.get_by_project_id(project_id):
            errors.append(f"Project ID '{project_id}' already exists")
        
        if errors:
            return None, errors
        
        try:
            project = ProjectDAO.create(
                name=name,
                pm_name=pm_name,
                project_id=project_id,
                bank_id=bank_id,
                project_link=project_link,
                start_date=start_date,
                end_date=end_date
            )
            return project, None
        except Exception as e:
            return None, [str(e)]
    
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
    ) -> Tuple[Optional[Project], Optional[List[str]]]:
        """Update project"""
        project = ProjectDAO.get_by_id(id)
        
        if not project:
            return None, ["Project not found"]
        
        errors = []
        
        # Check if new project_id already exists (for different project)
        if project_id and project_id != project.project_id:
            existing = ProjectDAO.get_by_project_id(project_id)
            if existing:
                errors.append(f"Project ID '{project_id}' already exists")
        
        if errors:
            return None, errors
        
        try:
            updated = ProjectDAO.update(
                id=id,
                name=name,
                pm_name=pm_name,
                project_id=project_id,
                bank_id=bank_id,
                project_link=project_link,
                start_date=start_date,
                end_date=end_date
            )
            return updated, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def add_members(
        project_id: str,
        members: List[Dict[str, Any]]
    ) -> Tuple[Optional[List[Any]], Optional[List[str]]]:
        """Add members to project with validation
        
        Args:
            project_id: UUID of the project
            members: List of dicts with keys: userId (or employeeId), allocationPercent
        
        Returns:
            Tuple of (created members list, errors list)
        """
        # Verify project exists
        project = ProjectDAO.get_by_id(project_id)
        if not project:
            return None, ["Project not found"]
        
        errors = []
        validated_members = []

        # Get existing member user IDs
        existing_user_ids = {str(member.user_id) for member in project.project_members}
        
        # Validate each member
        for idx, member in enumerate(members):
            user_id = member.get('userId')
            employee_id = member.get('employeeId')
            allocation = member.get('allocationPercent')
            
            # Must provide either userId or employeeId
            if not user_id and not employee_id:
                errors.append(f"Member {idx + 1}: userId or employeeId is required")
                continue
            
            # Validate allocation percentage
            if allocation is None:
                errors.append(f"Member {idx + 1}: allocationPercent is required")
                continue
            
            if not isinstance(allocation, int) or allocation < 0 or allocation > 100:
                errors.append(f"Member {idx + 1}: allocationPercent must be between 0 and 100")
                continue
            
            # Get employee UUID if employeeId provided
            if employee_id:
                employee = EmployeeDAO.get_by_employee_id(employee_id)
                if not employee:
                    errors.append(f"Member {idx + 1}: Employee '{employee_id}' not found")
                    continue
                user_id = str(employee.id)
            else:
                # Verify user_id exists
                employee = EmployeeDAO.get_by_id(user_id)
                if not employee:
                    errors.append(f"Member {idx + 1}: Employee with ID '{user_id}' not found")
                    continue
            
            # Check if user already exists in project
            if user_id in existing_user_ids:
                errors.append(f"Member {idx + 1}: Employee is already a member of this project")
                continue
            
            validated_members.append({
                'user_id': user_id,
                'allocation_percent': allocation
            })
        
        if errors:
            return None, errors
        
        try:
            created_members = ProjectDAO.add_members(project_id, validated_members)
            
            # Convert to response format
            result = [
                {
                    "id": str(member.id),
                    "userId": str(member.user_id),
                    "employeeId": member.employee.employeeId if member.employee else None,
                    "vnFullName": member.employee.vn_full_name if member.employee else None,
                    "enFullName": member.employee.en_full_name if member.employee else None,
                    "email": member.employee.email if member.employee else None,
                    "allocationPercent": member.allocation_percent,
                    "joinedAt": member.joined_at.isoformat() if member.joined_at else None
                }
                for member in created_members
            ]
            
            return result, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def _to_dict(project: Project, include_members: bool = False) -> Dict[str, Any]:
        """Convert project to dictionary"""
        result = {
            "id": str(project.id),
            "projectId": project.project_id,
            "name": project.name,
            "pmName": project.pm_name,
            "projectLink": project.project_link,
            "bankId": str(project.bank_id) if project.bank_id else None,
            "bankName": project.bank.name if project.bank else None,
            "createdAt": project.created_at.isoformat() if project.created_at else None,
            "startDate": project.start_date.isoformat() if project.start_date else None,
            "endDate": project.end_date.isoformat() if project.end_date else None
        }
        
        # Add members information if requested
        if include_members:
            result["members"] = [
                {
                    "id": str(member.id),
                    "userId": str(member.user_id),
                    "employeeId": member.employee.employeeId if member.employee else None,
                    "vnFullName": member.employee.vn_full_name if member.employee else None,
                    "enFullName": member.employee.en_full_name if member.employee else None,
                    "email": member.employee.email if member.employee else None,
                    "allocationPercent": member.allocation_percent,
                    "joinedAt": member.joined_at.isoformat() if member.joined_at else None,
                    "authorize_role": member.employee.authorize_role if member.employee else None,
                    "status": member.employee.status if member.employee else None
                    
                }
                for member in project.project_members
            ]
            result["memberCount"] = len(project.project_members)
        
        return result
        
    @staticmethod
    def _to_dict_with_members(project: Project) -> Dict[str, Any]:
        """Shortcut to get project dict with members"""
        return ProjectService._to_dict(project, include_members=True)


