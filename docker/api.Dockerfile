# Context: repo root
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy project files and restore
COPY src/backend/Directory.Build.props src/backend/
COPY src/backend/Hackathon.Api/Hackathon.Api.csproj src/backend/Hackathon.Api/
COPY src/backend/Hackathon.Application/Hackathon.Application.csproj src/backend/Hackathon.Application/
COPY src/backend/Hackathon.Domain/Hackathon.Domain.csproj src/backend/Hackathon.Domain/
COPY src/backend/Hackathon.Infrastructure/Hackathon.Infrastructure.csproj src/backend/Hackathon.Infrastructure/
COPY src/backend/Hackathon.ServiceDefaults/Hackathon.ServiceDefaults.csproj src/backend/Hackathon.ServiceDefaults/
RUN dotnet restore src/backend/Hackathon.Api/Hackathon.Api.csproj

# Copy source and publish
COPY src/backend/ src/backend/
RUN dotnet publish src/backend/Hackathon.Api/Hackathon.Api.csproj -c Release -o /app --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app .
EXPOSE 8080
ENTRYPOINT ["dotnet", "Hackathon.Api.dll"]
