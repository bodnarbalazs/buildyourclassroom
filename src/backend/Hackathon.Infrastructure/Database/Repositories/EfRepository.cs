using System.Linq.Expressions;
using Hackathon.Application.Shared.Repositories;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Hackathon.Infrastructure.Database.Repositories;

public partial class EfRepository<T> : IRepository<T> where T : class
{
#pragma warning disable CA1051
    protected readonly AppDbContext Context;
    protected readonly DbSet<T> DbSet;
    protected readonly ILogger<EfRepository<T>> Logger;
#pragma warning restore CA1051

    public EfRepository(AppDbContext context, ILogger<EfRepository<T>> logger)
    {
        Context = context;
        DbSet = context.Set<T>();
        Logger = logger;
    }

    public virtual async Task<IEnumerable<T>> GetAllAsync()
    {
        try { return await DbSet.ToListAsync(); }
        catch (Exception ex) { LogError(Logger, ex, "GetAll", typeof(T).Name); throw; }
    }

    public virtual async Task<IEnumerable<T>> GetByFilterAsync(Expression<Func<T, bool>> filter)
    {
        try { return await DbSet.Where(filter).ToListAsync(); }
        catch (Exception ex) { LogError(Logger, ex, "GetByFilter", typeof(T).Name); throw; }
    }

    public virtual async Task<T?> GetSingleByFilterAsync(Expression<Func<T, bool>> filter)
    {
        try { return await DbSet.FirstOrDefaultAsync(filter); }
        catch (Exception ex) { LogError(Logger, ex, "GetSingle", typeof(T).Name); throw; }
    }

    public virtual async Task<T?> GetByIdAsync(string id)
    {
        try
        {
            if (!Guid.TryParse(id, out _))
                throw new ArgumentException($"Invalid ID format: {id}", nameof(id));
            return await DbSet.FindAsync(id);
        }
        catch (Exception ex) { LogError(Logger, ex, "GetById", typeof(T).Name); throw; }
    }

    public virtual async Task<T> CreateAsync(T entity)
    {
        try
        {
            await DbSet.AddAsync(entity);
            await Context.SaveChangesAsync();
            return entity;
        }
        catch (Exception ex) { LogError(Logger, ex, "Create", typeof(T).Name); throw; }
    }

    public virtual async Task<T?> UpdateAsync(string id, T entity)
    {
        try
        {
            if (!Guid.TryParse(id, out _))
                throw new ArgumentException($"Invalid ID format: {id}", nameof(id));
            DbSet.Update(entity);
            await Context.SaveChangesAsync();
            return entity;
        }
        catch (Exception ex) { LogError(Logger, ex, "Update", typeof(T).Name); throw; }
    }

    public virtual async Task<bool> DeleteAsync(string id)
    {
        try
        {
            if (!Guid.TryParse(id, out _))
                throw new ArgumentException($"Invalid ID format: {id}", nameof(id));
            var entity = await DbSet.FindAsync(id);
            if (entity == null) return false;
            DbSet.Remove(entity);
            await Context.SaveChangesAsync();
            return true;
        }
        catch (Exception ex) { LogError(Logger, ex, "Delete", typeof(T).Name); throw; }
    }

    public virtual async Task<bool> ExistsAsync(Expression<Func<T, bool>> filter)
    {
        try { return await DbSet.AnyAsync(filter); }
        catch (Exception ex) { LogError(Logger, ex, "Exists", typeof(T).Name); throw; }
    }

    [LoggerMessage(Level = LogLevel.Error, Message = "Error in {Operation} for type {EntityType}")]
    private static partial void LogError(ILogger logger, Exception ex, string operation, string entityType);
}
