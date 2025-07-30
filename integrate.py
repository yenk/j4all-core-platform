"""
Integration script for LumiLens AI platform.

This script integrates the new FastAPI backend with the existing
Streamlit application and RAG pipeline, providing a smooth transition
and compatibility layer.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.config import settings
from api.services.vector_service import VectorService
from api.services.chat_service import ChatService
from api.core.logging import setup_logging


class LumiLensIntegration:
    """
    Integration manager for LumiLens platform components.
    
    Provides unified interface for managing both Streamlit and FastAPI
    components with shared services and data.
    """
    
    def __init__(self):
        """Initialize integration manager."""
        self.vector_service: Optional[VectorService] = None
        self.chat_service: Optional[ChatService] = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> None:
        """Initialize all platform services."""
        try:
            self.logger.info("🔧 Initializing LumiLens platform...")
            
            # Initialize vector service
            self.vector_service = VectorService()
            await self.vector_service.initialize()
            
            # Initialize chat service
            self.chat_service = ChatService()
            await self.chat_service.initialize()
            
            self.logger.info("✅ Platform initialization complete")
            
        except Exception as e:
            self.logger.error("❌ Platform initialization failed: %s", str(e))
            raise
    
    async def migrate_existing_data(self) -> None:
        """
        Migrate data from existing Streamlit setup to FastAPI.
        
        This ensures compatibility between the old Streamlit app
        and the new FastAPI backend.
        """
        try:
            self.logger.info("📦 Starting data migration...")
            
            if not self.vector_service:
                await self.initialize()
            
            # Check if data migration is needed
            stats = await self.vector_service.get_collection_stats()
            doc_count = stats.get("document_count", 0)
            
            if doc_count == 0:
                self.logger.info("📄 No existing documents found, running ingestion...")
                
                # Run document ingestion
                ingested_count = await self.vector_service.ingest_documents_from_directory()
                
                if ingested_count > 0:
                    self.logger.info("✅ Migrated %d documents", ingested_count)
                else:
                    self.logger.warning("⚠️ No documents found to migrate")
            else:
                self.logger.info("✅ Found %d existing documents, migration not needed", doc_count)
            
        except Exception as e:
            self.logger.error("❌ Data migration failed: %s", str(e))
            raise
    
    async def test_integration(self) -> bool:
        """
        Test integration between all components.
        
        Returns:
            bool: True if all tests pass
        """
        try:
            self.logger.info("🧪 Running integration tests...")
            
            if not self.vector_service or not self.chat_service:
                await self.initialize()
            
            # Test vector service
            health_ok = await self.vector_service.health_check()
            if not health_ok:
                self.logger.error("❌ Vector service health check failed")
                return False
            
            # Test chat service with sample query
            test_message = "What is this document about?"
            response, sources = await self.chat_service.generate_response(
                message=test_message,
                include_sources=True,
                max_sources=3
            )
            
            if not response:
                self.logger.error("❌ Chat service test failed")
                return False
            
            self.logger.info("✅ Integration tests passed")
            self.logger.info("📄 Test response: %s", response[:100] + "..." if len(response) > 100 else response)
            self.logger.info("📚 Found %d sources", len(sources))
            
            return True
            
        except Exception as e:
            self.logger.error("❌ Integration test failed: %s", str(e))
            return False
    
    async def start_services(self, service: str = "all") -> None:
        """
        Start platform services.
        
        Args:
            service: Service to start ("fastapi", "streamlit", "all")
        """
        try:
            self.logger.info("🚀 Starting services: %s", service)
            
            if service in ["fastapi", "all"]:
                await self._start_fastapi()
            
            if service in ["streamlit", "all"]:
                await self._start_streamlit()
            
        except Exception as e:
            self.logger.error("❌ Failed to start services: %s", str(e))
            raise
    
    async def _start_fastapi(self) -> None:
        """Start FastAPI server."""
        self.logger.info("🌐 Starting FastAPI server...")
        
        # Initialize services first
        await self.initialize()
        
        # Import and run server
        import uvicorn
        
        uvicorn.run(
            "api.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.ENVIRONMENT == "development",
            log_level="info" if settings.ENVIRONMENT == "development" else "warning"
        )
    
    async def _start_streamlit(self) -> None:
        """Start Streamlit app."""
        self.logger.info("🎨 Starting Streamlit app...")
        
        # Run existing Streamlit app
        import subprocess
        
        cmd = ["streamlit", "run", "app.py", "--server.port", "8501"]
        subprocess.run(cmd, cwd=project_root)
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self.logger.info("🧹 Cleaning up resources...")
            
            if self.vector_service:
                await self.vector_service.cleanup()
            
            self.logger.info("✅ Cleanup complete")
            
        except Exception as e:
            self.logger.error("❌ Cleanup failed: %s", str(e))


async def main():
    """
    Main integration script entry point.
    
    Handles command line arguments and orchestrates platform operations.
    """
    import argparse
    
    # Setup argument parser
    parser = argparse.ArgumentParser(description="LumiLens Platform Integration")
    parser.add_argument(
        "command",
        choices=["init", "migrate", "test", "start", "cleanup"],
        help="Command to execute"
    )
    parser.add_argument(
        "--service",
        choices=["fastapi", "streamlit", "all"],
        default="all",
        help="Service to operate on (for start command)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    logger = logging.getLogger(__name__)
    
    # Create integration manager
    integration = LumiLensIntegration()
    
    try:
        # Execute command
        if args.command == "init":
            logger.info("🔧 Initializing platform...")
            await integration.initialize()
            
        elif args.command == "migrate":
            logger.info("📦 Running data migration...")
            await integration.migrate_existing_data()
            
        elif args.command == "test":
            logger.info("🧪 Running integration tests...")
            success = await integration.test_integration()
            if not success:
                sys.exit(1)
                
        elif args.command == "start":
            logger.info("🚀 Starting services...")
            await integration.start_services(args.service)
            
        elif args.command == "cleanup":
            logger.info("🧹 Running cleanup...")
            await integration.cleanup()
        
        logger.info("✅ Command completed successfully")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Operation interrupted by user")
        await integration.cleanup()
        
    except Exception as e:
        logger.error("❌ Command failed: %s", str(e))
        await integration.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
