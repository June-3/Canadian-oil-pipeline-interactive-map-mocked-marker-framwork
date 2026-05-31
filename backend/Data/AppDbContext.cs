using Microsoft.EntityFrameworkCore;
using Backend.Models;

namespace Backend.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Asset> Assets => Set<Asset>();
    public DbSet<Reading> Readings => Set<Reading>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Asset>(entity =>
        {
            entity.ToTable("assets");
            entity.Property(e => e.Name).HasColumnName("name");
            entity.Property(e => e.Type).HasColumnName("type");
            entity.Property(e => e.Longitude).HasColumnName("longitude");
            entity.Property(e => e.Latitude).HasColumnName("latitude");
            entity.Property(e => e.Status).HasColumnName("status");
            entity.Property(e => e.UpdatedAt).HasColumnName("updated_at");
        });

        modelBuilder.Entity<Reading>(entity =>
        {
            entity.ToTable("readings");
            entity.Property(e => e.AssetId).HasColumnName("asset_id");
            entity.Property(e => e.Timestamp).HasColumnName("timestamp");
            entity.Property(e => e.Temperature).HasColumnName("temperature");
            entity.Property(e => e.Pressure).HasColumnName("pressure");
        });
    }
}
