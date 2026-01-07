resource "aws_ecr_repository" "stock_analyst" {
    name = "stock-analyst-repo"
    image_tag_mutability = "MUTABLE"

    image_scanning_configuration {
      scan_on_push = true
    }
}

output "repository_url" {
  value = aws_ecr_repository.stock_analyst.repository_url
}

# Lifecycle policy to ensure there is only one tagged image file, and untagged files are deleted
resource "aws_ecr_lifecycle_policy" "single_policy" {
  repository = aws_ecr_repository.stock_analyst.name
  
  policy = jsonencode({
    rules = [
        {
            rulePriority = 1
            description = "Keep only one tagged image"
            selection = {
                tagStatus = "tagged"
                tagPrefixList = ["latest"]
                countType = "imageCountMoreThan"
                countNumber = 1
            }
            action = {
                type = "expire"
            }
        },
        {
            rulePriority = 2
            description = "Immediately delete untagged images"
            selection = {
                tagStatus = "untagged"
                countType = "sinceImagePushed"
                countUnit = "days"
                countNumber = 1
            }
            action = {
                type = "expire"
            }
        }
    ]
  })
}