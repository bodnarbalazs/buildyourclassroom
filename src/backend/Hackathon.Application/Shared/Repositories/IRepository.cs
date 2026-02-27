using System.Linq.Expressions;

namespace Hackathon.Application.Shared.Repositories;

public interface IRepository<T> where T : class
{
    Task<IEnumerable<T>> GetAllAsync();
    Task<IEnumerable<T>> GetByFilterAsync(Expression<Func<T, bool>> filter);
    Task<T?> GetSingleByFilterAsync(Expression<Func<T, bool>> filter);
    Task<T?> GetByIdAsync(string id);
    Task<T> CreateAsync(T entity);
    Task<T?> UpdateAsync(string id, T entity);
    Task<bool> DeleteAsync(string id);
    Task<bool> ExistsAsync(Expression<Func<T, bool>> filter);
}
