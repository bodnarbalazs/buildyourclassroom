using Hackathon.Domain.Models.Auth;
using Microsoft.EntityFrameworkCore;

namespace Hackathon.Infrastructure.Database;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<User>(entity =>
        {
            entity.HasIndex(e => e.Email).IsUnique();
            entity.HasIndex(e => e.Username).IsUnique();
            entity.OwnsOne(e => e.Password);
            entity.Property(e => e.RefreshTokens).HasColumnType("jsonb");
            entity.Property(e => e.Roles).HasColumnType("jsonb");
        });
    }
}
